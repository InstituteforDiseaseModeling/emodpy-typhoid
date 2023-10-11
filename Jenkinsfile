podTemplate(
    //idleMinutes : 30,
    podRetention : onFailure(),
    activeDeadlineSeconds : 3600,
    containers: [
        containerTemplate(
            name: 'dtk-rpm-builder', 
            image: 'docker-production.packages.idmod.org/idm/dtk-rpm-builder:0.1',
            command: 'sleep', 
            args: '30d'
            )
  ]) {
  properties([
            parameters([
                gitParameter(branch: '',
                             branchFilter: 'origin/(.*)',
                             defaultValue: 'main',
                             description: '',
                             name: 'BRANCH',
                             quickFilterEnabled: false,
                             selectedValue: 'NONE',
                             sortMode: 'NONE',
                             tagFilter: '*',
                             type: 'PT_BRANCH'),
                gitParameter(branch: '',
                            branchFilter: '.*',
                            defaultValue: '-1',
                            name: 'PR',
                            quickFilterEnabled: false,
                            selectedValue: 'NONE',
                            sortMode: 'NONE',
                            tagFilter: '*',
                            type: 'PT_PULL_REQUEST'),
                choice(choices: ['Code', 'Production', 'Staging'], name: 'typhoid_environment'),
                string(defaultValue: '-1', name: 'emodpy_version'),
                choice(choices: ['Production', 'Staging'], name: 'emodpy_environment'),
                string(defaultValue: '-1', name: 'emodapi_version'),
                choice(choices: ['Production', 'Staging'], name: 'emodapi_environment')

        ])])
  node(POD_LABEL) {
    container('dtk-rpm-builder'){
		def build_ok = true
		stage('Cleanup Workspace') {
			cleanWs()
			echo "Cleaned Up Workspace For Project"
			echo "${params.BRANCH}"
		}
		stage('Prepare') {
			sh 'python --version'
			sh 'python3 --version'
			sh 'pip3 --version'

			sh 'python3 -m pip install --upgrade pip'
			sh "pip3 install wheel unittest-xml-reporting pytest"
			sh 'python3 -m pip install --upgrade setuptools'
			sh 'pip3 freeze'
		}
		stage('Code Checkout') {
			if (params.PR.toString() != '-1') {
				echo "I execute on the pull request ${params.PR}"
				checkout([$class: 'GitSCM',
				branches: [[name: "pr/${params.PR}/head"]],
				doGenerateSubmoduleConfigurations: false,
				extensions: [],
				gitTool: 'Default',
				submoduleCfg: [],
				userRemoteConfigs: [[refspec: '+refs/pull/*:refs/remotes/origin/pr/*', credentialsId: '704061ca-54ca-4aec-b5ce-ddc7e9eab0f2', url: 'git@github.com:InstituteforDiseaseModeling/emodpy-typhoid.git']]])
			} else {
				echo "I execute on the ${params.BRANCH} branch"
				git branch: "${params.BRANCH}",
				credentialsId: '704061ca-54ca-4aec-b5ce-ddc7e9eab0f2',
				url: 'git@github.com:InstituteforDiseaseModeling/emodpy-typhoid.git'
			}
		}
		stage('Install, login') {
			def curDate = sh(returnStdout: true, script: "date").trim()
			echo "The current date is ${curDate}"

			if (params.typhoid_environment == 'Staging') {
				echo "I am installing emodpy-typhoid from Staging"
				withCredentials([string(credentialsId: 'idm_bamboo_user', variable: 'user'), string(credentialsId: 'idm_bamboo_user_password', variable: 'password')]) {
					sh 'pip3 install emodpy-typhoid --index-url=https://$user:$password@packages.idmod.org/api/pypi/pypi-staging/simple'
				}

			 } else if (params.typhoid_environment == 'Production'){
				 echo "I am installing emodpy-typhoid from Production"
				 sh 'pip3 install emodpy-typhoid --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple'
			 } else {
				echo "I am installing emodpy-typhoid from code"
				sh "pip3 install -r requirements_2018.txt --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple"
				sh "pip3 list"
				sh "pip3 install -e ."
				sh "pip3 list"
			 }
			if (params.emodpy_version != '-1') {
			    def version = params.emodpy_version
				echo "I am re-installing emodpy==${version} from ${params.emodpy_environment}"

				if (params.emodpy_environment == 'Staging') {
					withCredentials([string(credentialsId: 'idm_bamboo_user', variable: 'user'), string(credentialsId: 'idm_bamboo_user_password', variable: 'password')]) {
						sh "pip3 install emodpy==${version} --index-url=https://$user:$password@packages.idmod.org/api/pypi/pypi-staging/simple --force-reinstall --no-cache-dir"
					}
				} else {
				    sh "pip3 install emodpy==${version} --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple --force-reinstall --no-cache-dir"
				}
			}
			if (params.emodapi_version != '-1') {
				def api_version = params.emodapi_version
				echo "I am re-installing emodapi==${api_version} from ${params.emodapi_environment}"

				if (params.emodapi_environment == 'Staging') {
					withCredentials([string(credentialsId: 'idm_bamboo_user', variable: 'user'), string(credentialsId: 'idm_bamboo_user_password', variable: 'password')]) {
						sh "pip3 install emod-api==${api_version} --index-url=https://$user:$password@packages.idmod.org/api/pypi/pypi-staging/simple --force-reinstall --no-cache-dir"
					}
				} else {
				    sh "pip3 install emod-api==${api_version} --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple --force-reinstall --no-cache-dir"
				}
			}
			sh "pip3 install dataclasses"
			sh 'pip3 install keyrings.alt'
			sh "pip3 freeze"
			withCredentials([usernamePassword(credentialsId: 'comps_jenkins_user', usernameVariable: 'COMPS_USERNAME', passwordVariable: 'COMPS_PASSWORD'),
			                 usernamePassword(credentialsId: 'comps2_jenkins_user', usernameVariable: 'COMPS2_USERNAME', passwordVariable: 'COMPS2_PASSWORD'),
			                 string(credentialsId: 'Bamboo_id', variable: 'bamboo_user'), string(credentialsId: 'Bamboo', variable: 'bamboo_password')]) {
				sh 'python3 .dev_scripts/create_auth_token_args.py --comps_url https://comps2.idmod.org --username $COMPS2_USERNAME --password $COMPS2_PASSWORD'
		        sh 'python3 .dev_scripts/create_auth_token_args.py --comps_url https://comps.idmod.org --username $COMPS_USERNAME --password $COMPS_PASSWORD'
			}
		}
			
		try{
			stage('Unit Test') {
				echo "Running Unit test Tests"
				dir('tests/unittests') {
					sh 'py.test -sv --junitxml=reports/test_results.xml'
					junit 'reports/*.xml'
				}
			}
		} catch(e) {
			build_ok = false
			echo e.toString()
		}

		try{
			stage('Workflow Test') {
				echo "Running Workflow Tests"
				dir('tests/workflow_tests') {
				    sh 'py.test -sv --junitxml=reports/test_results.xml'
				    junit 'reports/*.xml'
				}
			}
		} catch(e) {
			build_ok = false
			echo e.toString()
		}

    // 	stage('Run Examples') {
    // 		echo "Running examples"
    // 			dir('examples') {
				// sh 'pip3 install snakemake'
    //               		sh 'snakemake --cores=4 --config python_version=python3'
    // 			}
    // 		}
    	if(build_ok) {
    		currentBuild.result = "SUCCESS"
    	} else {
    		currentBuild.result = "FAILURE"
    	}
	}
 }
}
