pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: sonar-scanner
    image: sonarsource/sonar-scanner-cli
    command: ["cat"]
    tty: true
    volumeMounts:
    - name: workspace-volume
      mountPath: /home/jenkins/agent

  - name: kubectl
    image: bitnami/kubectl:latest
    command: ["cat"]
    tty: true
    securityContext:
      runAsUser: 0
      readOnlyRootFilesystem: false
    env:
    - name: KUBECONFIG
      value: /kube/config
    volumeMounts:
    - name: kubeconfig-secret
      mountPath: /kube/config
      subPath: kubeconfig
    - name: workspace-volume
      mountPath: /home/jenkins/agent

  - name: dind
    image: docker:dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    volumeMounts:
    - name: docker-config
      mountPath: /etc/docker/daemon.json
      subPath: daemon.json
    - name: workspace-volume
      mountPath: /home/jenkins/agent
    - name: workspace-volume
      mountPath: /app

  volumes:
  - name: docker-config
    configMap:
      name: docker-daemon-config
  - name: kubeconfig-secret
    secret:
      secretName: kubeconfig-secret
  - name: workspace-volume
    emptyDir: {}
'''
        }
    }

    environment {
        APP_NAME       = "2401082-videosummdocker"
        IMAGE_TAG      = "latest"
        REGISTRY_URL   = "nexus-service-for-docker-hosted-registry.nexus.svc.cluster.local:8085"
        REGISTRY_REPO  = "2401082-videosummdocker"
        SONAR_PROJECT  = "2401082-videosummdocker"
        SONAR_HOST_URL = "http://my-sonarqube-sonarqube.sonarqube.svc.cluster.local:9000"
    }

    stages {

        stage('Build Docker Image') {
            steps {
                container('dind') {
                    sh '''
                        sleep 15
                        docker build -t $APP_NAME:$IMAGE_TAG .
                        docker images
                    '''
                }
            }
        }

        stage('Run Tests in Docker') {
            steps {
                container('dind') {
                    sh '''
                        docker run --rm -v $(pwd):/workspace -w /app $APP_NAME:$IMAGE_TAG \
                        sh -c "pytest --maxfail=1 --disable-warnings --cov=. --cov-report=xml && cp coverage.xml /workspace/coverage.xml"
                    '''
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                container('sonar-scanner') {
                    withCredentials([
                        string(credentialsId: '2401082-videosummdocker', variable: 'SONAR_TOKEN')
                    ]) {
                        sh '''
                            sonar-scanner \
                              -Dsonar.projectKey=$SONAR_PROJECT \
                              -Dsonar.host.url=$SONAR_HOST_URL \
                              -Dsonar.token=$SONAR_TOKEN \
                              -Dsonar.python.coverage.reportPaths=coverage.xml
                        '''
                    }
                }
            }
        }

        stage('Login to Docker Registry') {
            steps {
                container('dind') {
                    sh '''
                        docker --version
                        sleep 10
                        echo "Changeme@2025" | docker login $REGISTRY_URL -u admin --password-stdin
                    '''
                }
            }
        }

        stage('Build - Tag - Push Image') {
            steps {
                container('dind') {
                    sh '''
                        docker tag $APP_NAME:$IMAGE_TAG \
                          $REGISTRY_URL/$REGISTRY_REPO/$APP_NAME:$IMAGE_TAG

                        docker push $REGISTRY_URL/$REGISTRY_REPO/$APP_NAME:$IMAGE_TAG
                    '''
                }
            }
        }

        stage('Deploy Application') {
            steps {
                container('kubectl') {
                    dir('k8s') {
                        sh '''
                            kubectl apply -f namespace.yaml

                            kubectl create secret docker-registry regcred \
                              --docker-server=$REGISTRY_URL \
                              --docker-username=admin \
                              --docker-password=Changeme@2025 \
                              --docker-email=jenkins@example.com \
                              -n 2401082-videosummdocker \
                              --dry-run=client -o yaml | kubectl apply -f -

                            kubectl apply -f service.yaml
                            kubectl apply -f deployment.yaml
                            kubectl apply -f ingress.yaml

                            kubectl rollout restart deployment/$APP_NAME -n 2401082-videosummdocker
                            kubectl rollout status deployment/$APP_NAME -n 2401082-videosummdocker --timeout=10m
                        '''
                    }
                }
            }
        }
    }
}
