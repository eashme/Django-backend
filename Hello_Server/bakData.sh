#!/bin/bash
# 在服务器上的存放路径为 /root/data_bak/script

DATE=`date +%Y-%m-%d`
BACKUP_FILE=/root/data_bak/WHALE.server.data.bak.${DATE}.json  #备份数据文件的路径
PROJECT_DIR=/root/Hellocial/current_project/Hellocial_0_1/  #项目目录
VIRTUAL_ENV=/root/env/whela/bin/activate  # 虚拟环境


send_email(){

    echo "Send email"

    python send_data_bak.py  # 直接运行发邮件的python程序,这个程序我放在项目目录下,所以就不再切换目录了

    echo "Send ok!"
}


bak_data(){

    echo "bak data"

    python manage.py dumpdata --exclude=contenttypes --exclude=auth.Permission --format=json > $BACKUP_FILE  # 备份数据

    echo "bak OK!"
}

main(){
    source $VIRTUAL_ENV  # 激活虚拟环境

    cd $PROJECT_DIR  # 切换到项目目录

    bak_data

    if [ -e "$BACKUP_FILE" ]
    then
        send_email
    else
        echo "Fail to bak data."
    fi

}

main