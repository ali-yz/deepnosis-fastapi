# set variables
USER_NAME="ubuntu"
HOSTNAME="37.32.14.236"
PRIVATE_KEY_PATH="/c/Users/ASUS/.ssh/ar-ArvanSSHAli-privatekey.pem"

# use scp to copy the file to the server in app directory
scp -o StrictHostKeyChecking=no -i ${PRIVATE_KEY_PATH} -r ./* ${USER_NAME}@${HOSTNAME}:/home/${USER_NAME}/app

echo "Files copied"

# use ssh to run commands on the server
ssh -o StrictHostKeyChecking=no -i ${PRIVATE_KEY_PATH} ${USER_NAME}@${HOSTNAME} '

    # Say hi
    echo "Hi Ali"

    # kill the running app on port 80
    sudo kill $(sudo lsof -t -i:80)

    # activate the virtual environment
    source myenv/bin/activate

    # print process id
    echo $(sudo lsof -t -i:80)

    # use uvicorn to run the app on port 80 non-blocking
    sudo nohup /home/ubuntu/myenv/bin/python3 -m uvicorn app.app:app --host 0.0.0.0 --port 80 > /home/ubuntu/uvicorn.log 2>&1 &

    # print process id
    echo $(sudo lsof -t -i:80)
    '