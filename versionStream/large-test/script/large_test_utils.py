import yaml
from datetime import datetime
import os


def get_versions(result, namespace):
    with open('helmfile.yaml', 'r') as helmfile:
        items = yaml.load(helmfile, Loader=yaml.FullLoader)
        for item in items['releases']:
            if item['chart'].startswith('dev/') and item['namespace'] == 'jx-' + namespace:
                result.append({'name': item['name'], 'version': item['version']})
    return result


def store_versions():
    result = {}
    result['status'] = os.environ['TEST_STATUS']
    result['sha'] = os.environ['GIT_SHA']
    result['largeTestImages'] = [{'large-tests': os.environ['LARGE_REPORTS_IMAGE']}]
    result['testResultUrl'] = os.environ['REPORTS_URL'] + '/' + os.environ['ENV'] + '_' + os.environ['GIT_SHA'] + "/"
    result['commit'] = os.environ['REPO_URL'].replace('.git', '') + '/commit/' + os.environ['GIT_SHA']
    result['timestamp'] = datetime.today()
    result['environment'] = os.environ['ENV']
    result['versions'] = []
    get_versions(result['versions'], os.environ['ENV'])

    with open('.execution.info', 'w') as resultFile:
        yaml.safe_dump(result, resultFile)

    with open(os.environ['REPORT_FOLDER'] + '/.test-results.yaml', 'a') as resultFile:
        yaml.safe_dump([result], resultFile)


def check_versions():
    deployed_app_versions = []
    env_to_test = []

    with open('.deployed_apps', 'r') as deployed_apps:
        fields = deployed_apps.readline().split()
        for row in deployed_apps:
            app = {}
            for index, record in enumerate(row.split()):
                app[fields[index].lower()] = record
            deployed_app_versions.append(app)

    with open('helmfile.yaml', 'r') as helmfile:
        items = yaml.load(helmfile, Loader=yaml.FullLoader)
        for item in items['releases']:
            if item['chart'].startswith('dev/'):
                if not search_version(deployed_app_versions, item):
                    env_to_test.append(item['namespace'].replace('jx-', ''))

    env_to_test = set(env_to_test)
    print(env_to_test)
    failed = False
    for env in env_to_test:
        with open('.environments', 'r') as environments_file:
            environments = yaml.load(environments_file, Loader=yaml.FullLoader)
            environment_order = []
            for item in environments['items']:
                if 'order' in item['spec']:
                    environment_order.append({'name': item['metadata'].get('name'), 'order': item['spec']['order']})
                else:
                    environment_order.append({'name': item['metadata'].get('name'), 'order': 0})
        environment_order = sorted(environment_order, key=lambda x: x['order'])
        environment_index = 0
        for index, environment in enumerate(environment_order):
            if environment['name'] == env:
                environment_index = index
                break
        previous_env = None
        for index in list(range(environment_index - 1, -1, -1)):
            if environment_order[index]['order'] != 0 \
                    and environment_order[index]['order'] < environment_order[environment_index]['order']:
                previous_env = environment_order[index]['name']
                break

        versions = []
        if previous_env is not None:
            print('Performing check of test run on ' + previous_env + ' environment to verify promotion on ' + env)
            get_versions(versions, env)
            last_test_run = get_last_test_run(previous_env, versions)
            print(last_test_run)
            if last_test_run is None:
                print('Large test check not found for ' + env)
                failed = True
            else:
                print('Large test check for ' + previous_env + ' has status ' + last_test_run['status'])
                if last_test_run['status'] == 'failed':
                    failed = True
            if failed:
                break
        else:
            with open('.test_status', 'w') as testStatus:
                print('Check skipped for ' + env + ' because previous environment is not eligible for testing')

    if not failed:
        print('Large tests check for all version on all environments passed: ' + repr(env_to_test))

    with open('.test_status', 'w') as testStatus:
        testStatus.write('False' if failed else 'True')


def update_promotion_label():
    os.mknod(".promotion_label")
    with open('pr.yaml', 'r') as pr:
        pr_yaml = yaml.load(pr, Loader=yaml.FullLoader)
        for label in pr_yaml['Labels']:
            if label['Name'].startswith('env/'):
                with open('.promotion_label', 'w') as promotion_label:
                    promotion_label.write(label['Name'].replace('env/', ''))


def check_promotion():
    deployed_app_versions = []
    env_to_test = []
    with open('.deployed_apps', 'r') as deployed_apps:
        fields = deployed_apps.readline().split()
        for row in deployed_apps:
            app = {}
            for index, record in enumerate(row.split()):
                app[fields[index].lower()] = record
            deployed_app_versions.append(app)

    with open('helmfile.yaml', 'r') as helmfile:
        items = yaml.load(helmfile, Loader=yaml.FullLoader)
        for item in items['releases']:
            if item['chart'].startswith('dev/'):
                if not search_version(deployed_app_versions, item):
                    env_to_test.append(item['namespace'].replace('jx-', ''))
    print(env_to_test)
    if len(env_to_test) == 0:
        env_to_test.append('staging')
    print(set(env_to_test))
    os.mknod(".env_to_test")
    with open('.env_to_test', 'w') as env_to_test_file:
        env_to_test_file.write('\n'.join(set(env_to_test)))
        env_to_test_file.write('\n')


def search_version(versions, app):
    for version in versions:
        if app['name'] == version['application'] \
                and app['namespace'].replace('jx-', '') in version \
                and app['version'] == version[app['namespace'].replace('jx-', '')]:
            return True
    return False


def print_comment():
    with open('.environments', 'r') as environments_file:
        environments = yaml.load(environments_file, Loader=yaml.FullLoader)
        promotion_environments = []
        for item in environments['items']:
            if item['spec'].get('promotionStrategy') != 'Never':
                promotion_environments.append(item['metadata'].get('name'))

    for env in promotion_environments:
        versions = []
        get_versions(versions, env)

        status = None
        last_test_run = get_last_test_run(env, versions)
        if last_test_run is not None:
            status = last_test_run['status']

        tests_execution_status = None
        if status is None:
            tests_execution_status = 'Not Found'
        else:
            tests_execution_status = status

        print('Environment **' + env + '** with last **large tests** execution status: **' + tests_execution_status + '**')

        print('')
        print('| Name | Version |')
        print('| ---- | ------- |')

        for item in versions:
            print('| ', item['name'], ' | ', item['version'], ' |')

        print('')


def get_last_test_run(env, versions):
    test_runs = []
    with open(os.environ['REPORT_FOLDER'] + '/.test-results.yaml', 'r') as results:
        test_results = yaml.load(results, Loader=yaml.FullLoader)
        for test_result in test_results:
            if sorted(test_result['versions'], key=lambda k: k['name']) == sorted(versions, key=lambda k: k['name']) \
                    and test_result['environment'] == env:
                test_runs.append(test_result)
    last_test_run = None
    if len(test_runs) != 0:
        test_run = sorted(test_runs, key=lambda k: k['timestamp'])[len(test_runs) - 1]
        last_test_run = test_run
    return last_test_run
