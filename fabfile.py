from fabric.contrib.files import append, exists, sed, put
from fabric.api import local, run, sudo, env
import os
import json

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
print(PROJECT_DIR)

envs = json.load(open(os.path.join(PROJECT_DIR, 'deploy.json')))
print(envs)
'''
    "REPO_URL"  : "https://github.com/jungmannn/first.git",
    "PROJECT_NAME"  : "first",
    "REMOTE_HOST"  : "ec2-52-79-160-167.ap-northeast-2.compute.amazonaws.com",
    "REMOTE_HOST_SSH"  : "52.79.160.167",
    "REMOTE_USER" : "ubuntu"
'''

REPO_URL = envs['REPO_URL']  
PROJECT_NAME = envs['PROJECT_NAME']    
REMOTE_HOST = envs['REMOTE_HOST']    
REMOTE_HOST_SSH = envs['REMOTE_HOST_SSH']  
REMOTE_USER = envs['REMOTE_USER']

env.user = REMOTE_USER
env.hosts = [
        REMOTE_HOST_SSH,
    ]

env.use_ssh_config = True
env.key_filename = 'jungman.pem'

project_folder = '/home/{}/{}'.format(env.user, PROJECT_NAME)
print(project_folder)


apt_requirements = [
    'curl',
    'git',
    'python3-pip',
    'python3-dev',
    'build-essential',
    'apache2',
    'libapache2-mod-wsgi-py3',
    'python3-setuptools',
    'libssl-dev',
    'libffi-dev'
]


'''
    작성이 모두 끝난 후
    > fab new_initServer
    소스가 변경된 후
    > fab update
'''

def newInitServer():
    _setup()
    update()


def _setup():
    _init_apt()
    _install_apt_packages( apt_requirements )
    _making_virtualenv()
    
def _init_apt():
    yn = input('ubuntu linux update ok? : [y/n]')
    if yn == 'y':
        sudo('apt-get update && apt-get -y upgrade')

def _install_apt_packages(requires):
    reqs = ''
    for req in requires:
        reqs += ' ' + req
    sudo('apt-get -y install' + reqs)

def _making_virtualenv():
    if not exists('~/.virtualenvs'):
        
        # 가상환경폴더
        # run 구동 > ubuntu 소유
        # sudo 구동 > root 소유
        run('mkdir ~/.virtualenvs')
        # 패키지 설치
        sudo('pip3 install virtualenv virtualenvwrapper')
        # 환경변수 반영 및 쉘(윈도우의 배치) 구동 가상환경 구축
        cmd = '''
            "# python virtualenv global setting
            export WORKON_HOME = ~/.virtualenvs
            # ptyhon location
            export VIRTUALENVWRAPPER_PYTHON = "$(command \which python3)"
            # shell 실행
            source /usr/local/bin/virtualenvwrapper.sh"
        '''
        run('echo {} >> ~/.bashrc'.format(cmd))

def update():
    _git_update()
    _virtualenv_update()
    _virtualhost_make()
    _grant_apache()
    _restart_apache()

def _git_update():
    if exists(project_folder + '/.git'):
        run('cd %s && git fetch' % (project_folder,))
    else:
        run('git clone %s %s' % (REPO_URL, project_folder))
    current_commit = local("git log -n 1 --format=%H", capture=True)
    run('cd %s && git reset --hard %s' % (project_folder, current_commit))

def _virtualenv_update():
    virtualenv_folder = project_folder + '/../.virtualenvs/{}'.format(PROJECT_NAME)
    if not exists(virtualenv_folder + '/bin/pip'):
        run('cd /home/%s/.virtualenvs && virtualenv %s' % (env.user, PROJECT_NAME))
    run('%s/bin/pip install -r %s/requirements.txt' % (
        virtualenv_folder, project_folder
    ))

def _ufw_allow():
    sudo("ufw allow 'Apache Full'")
    sudo("ufw reload")

def _virtualhost_make():
    script = """'
    <VirtualHost *:80>
        ServerName {servername}
        <Directory /home/{username}/{project_name}>
            <Files wsgi.py>
                Require all granted
            </Files>
        </Directory>
        WSGIDaemonProcess {project_name} python-home=/home/{username}/.virtualenvs/{project_name} python-path=/home/{username}/{project_name}
        WSGIProcessGroup {project_name}
        WSGIScriptAlias / /home/{username}/{project_name}/wsgi.py
        
        ErrorLog ${{APACHE_LOG_DIR}}/error.log
        CustomLog ${{APACHE_LOG_DIR}}/access.log combined

    </VirtualHost>'""".format(
        username=REMOTE_USER,
        project_name=PROJECT_NAME,
        servername=REMOTE_HOST,
    )
    sudo('echo {} > /etc/apache2/sites-available/{}.conf'.format(script, PROJECT_NAME))
    sudo('a2ensite {}.conf'.format(PROJECT_NAME))

def _grant_apache():
    sudo('chown -R :www-data ~/{}'.format(PROJECT_NAME))
    sudo('chmod -R 775 ~/{}'.format(PROJECT_NAME))

def _restart_apache():
     sudo('service apache2 restart')