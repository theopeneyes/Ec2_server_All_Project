#!/bin/bash
cd /home/ec2-user/AIG-Llama2_Video
source environment/bin/activate
echo "starting application" >> /home/ec2-user/startup.log
nohup uvicorn main:app --reload --port 8080 >> /home/ec2-user/startup.log 2>&1 &
