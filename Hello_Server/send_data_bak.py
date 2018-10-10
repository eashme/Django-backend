# -*- coding: UTF-8 -*-
# 该文件服务端路径为: /root/Hellocial/current_project/Hellocial_0_1/send_data_bak.py

import datetime, smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


def get_date(file_name):
    return datetime.datetime.strptime(file_name.split('.')[-2], '%Y-%m-%d')


def get_max_date(file_name1, file_name2):
    date1 = get_date(file_name1)
    date2 = get_date(file_name2)

    if date1 > date2:
        return file_name1
    else:
        return file_name2


def get_max_date_bak(path):
    """
    传入要查找的路径,
    返回最新的备份文件名称
    :param path:
    :return:
    """
    bak_file = None
    for i, file_name in enumerate(os.listdir(path)):
        if file_name.startswith('WHALE.server.data.bak.'):
            if i == 0:
                bak_file = file_name
            try:
                bak_file = get_max_date(file_name, bak_file)
            except Exception:
                continue

    return bak_file


def send_email(path, subject, content, from_email, to_addr):
    message = MIMEMultipart()

    bak_file = 'WHALE.server.data.bak.%s.json' % datetime.datetime.now().date().strftime('%Y-%m-%d')

    try:
        # 构造附件1，传送当前目录下的 test.txt 文件
        att1 = MIMEText(open(path + bak_file, 'rb').read(), 'base64', 'utf-8')
        att1["Content-Type"] = 'application/octet-stream'
        # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
        att1["Content-Disposition"] = 'attachment; filename="%s"' % bak_file
        message.attach(att1)
    except Exception as e:
        subject = '备份失败,脚本出问题了,快找jack'
        content = '备份失败 (reason: %s)' % e

    message['From'] = Header("jake", 'utf-8')
    message['To'] = Header('leon', 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')
    # 邮件正文内容
    message.attach(MIMEText(content, _charset='utf-8'))

    try:
        smtp = smtplib.SMTP_SSL(host='smtp.exmail.qq.com', port=465, timeout=20)
        smtp.login(from_email, 'Ws13429830518')
        smtp.sendmail(from_addr=from_email, to_addrs=to_addr, msg=message.as_string())
        smtp.quit()
    except smtplib.SMTPException as e:
        with open('error.log', 'a+') as f:
            f.write('[time] %s:\n' % str(datetime.datetime.now().date()))
            f.write('[ERROR]Fail to send email! (%s)' % e)


def main():
    path = "/root/data_bak/"
    subject = 'WHALE系统后台数据备份%s' % str(datetime.datetime.now().date())
    content = """
        数据库备份JSON格式文件,在项目文件中使用　“python manage.py loaddata 此文件的路径”　　命令即可恢复数据,无数据库类型要求.
        如果是新机器,要先创建好对应的数据库,然后使用python manage.py migrate 命令先将项目和数据库进行同步
        """
    from_email = 'xxxx@163.com'
    to_addr = ['xxxx@163.com']
    send_email(path, subject=subject, content=content, from_email=from_email, to_addr=to_addr)


if __name__ == "__main__":
    main()
