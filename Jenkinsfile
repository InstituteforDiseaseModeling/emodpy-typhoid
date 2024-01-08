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
			sh 'pip3 install wheel unittest-xml-reporting pytest'
			sh 'python3 -m pip install --upgrade setuptools'
			sh 'pip3 freeze'
		}
		stage('Code Checkout') {
			if (env.CHANGE_ID) {
				echo "I execute on the pull request ${env.CHANGE_ID}"
				checkout([$class: 'GitSCM',
				branches: [[name: "pr/${env.CHANGE_ID}/head"]],
				doGenerateSubmoduleConfigurations: false,
				extensions: [],
				gitTool: 'Default',
				submoduleCfg: [],
				userRemoteConfigs: [[refspec: '+refs/pull/*:refs/remotes/origin/pr/*', credentialsId: '704061ca-54ca-4aec-b5ce-ddc7e9eab0f2', url: 'git@github.com:InstituteforDiseaseModeling/emodpy-typhoid.git']]])
			} else {
				echo "I execute on the ${env.BRANCH_NAME} branch"
				git branch: "${env.BRANCH_NAME}",
				credentialsId: '704061ca-54ca-4aec-b5ce-ddc7e9eab0f2',
				url: 'git@github.com:InstituteforDiseaseModeling/emodpy-typhoid.git'
            }
        }
		stage('Install') {
			def curDate = sh(returnStdout: true, script: "date").trim()
			echo "The current date is ${curDate}"
			echo "I am installing emodpy-typhoid from github source code"
			sh "pip3 install -r requirements_2018.txt --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple"
			sh "pip3 list"
			sh "pip3 install -e ."
			sh "pip3 list"
		}
		stage('Login') {
			withCredentials([usernamePassword(credentialsId: 'comps_jenkins_user', usernameVariable: 'COMPS_USERNAME', passwordVariable: 'COMPS_PASSWORD'),
					         usernamePassword(credentialsId: 'comps2_jenkins_user', usernameVariable: 'COMPS2_USERNAME', passwordVariable: 'COMPS2_PASSWORD')])
			{
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
		try{
			stage('SFT Test') {
				echo "Running SFT Tests"
				dir('tests/sft_tests') {
				    sh 'pip3 install idm-test>=0.1.2 --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple'
				    sh 'python3 run_all_sft_tests.py'
				    junit '**/test_results.xml'
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
