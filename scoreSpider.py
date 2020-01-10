# ！/user/bin/env python
# -*- coding:utf-8 -*-
'''
Created on 2019-1-1
爬取正方教务系统成绩
@author: auko
'''

from requests import packages, session, post
from urllib.parse import quote
from requests.exceptions import RequestException
from os import system
from http.cookiejar import LWPCookieJar
from schedule import every, run_pending, clear
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.utils import formataddr
from re import search, findall
from time import sleep

# 取消未验证证书警告
packages.urllib3.disable_warnings()
s = session()
# cookie托管给cookiejar
s.cookies = LWPCookieJar(filename='./cookies.txt')


class scoreSpider:
    def __init__(self):
        # 通过识别两种不同的编码来判断是否连接了校园网
        self.charset = 'gb2312'  # 正常登陆页编码方式
        self.certificationPageCharset = 'UTF-8'  # 验证页编码方式
        self.loginUrl = 'https://jwc.scnu.edu.cn/default2.aspx'
        self.checkCodeUrl = 'https://jwc.scnu.edu.cn/CheckCode.aspx'
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
        self.host = 'jwc.scnu.edu.cn'
        self.headers = { # headers要设置好, 否则会重定向(反爬策略之一)
            'user-agent': self.user_agent,
            'Host': self.host,
            'Referer': self.loginUrl,
        }
        self.name = ''
        self.loginForm = {
            '__VIEWSTATE': '',
            'txtUserName': 0,
            'Textbox1': '',
            'TextBox2': '',
            'txtSecretCode': '',
            'RadioButtonList1': u'学生'.encode('gb2312'),
            'Button1': '',
            'lbLanguage': '',
            'hidPdrs': '',
            'hidsc': '',
        }
        self.hasTemp = self.get_temp()
        self.InternalVIEWSTATE = ''
        self.scoreUrl = 'https://jwc.scnu.edu.cn/xscjcx.aspx?xh=' + str(
            self.loginForm['txtUserName']
        ) + '&xm=' + self.name + '&gnmkdm=N121605'
        self.scoreHeaders = {
            'user-agent': self.user_agent,
            'Host': self.host,
            'Referer': self.scoreUrl
        }
        self.scoreForm = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': self.InternalVIEWSTATE,
            'hidLanguage': '',
            'ddl_kcxz': ''
        }
        self.ignoreItem = [2, 4, 5, 13, 14, 15, 16, 17, 18]
        self.preNum = 0
        self.timer = every(5).to(7).minutes.do(
            self.monitor).tag('monitor-score')
        self.sender = 'aukocharlie@qq.com'  # 发件人邮箱账号,按需换成自己的
        self.MailPass = 'xxxxxxxxxx'  # smtp授权码,按需换成自己的
        self.aimMail = ''  # 收件人邮箱账号
        self.needSend = False

    # 获取temp.txt里保存的信息, 包括学号和姓名, 是自动登录时需要的信息
    def get_temp(self):
        try:
            with open('./temp.txt', 'r', encoding='gbk') as f:
                txtUserName = f.readline()
                name = f.readline()
                if txtUserName and name:
                    self.loginForm['txtUserName'] = txtUserName[
                        txtUserName.find('=') + 1:].replace('\r', '').replace(
                            '\n', '')
                    self.name = quote(name[name.find('=') + 1:].replace(
                        '\r', '').replace('\n', '').encode('gbk'))
                    return True
                else:
                    return False
        except FileNotFoundError as e:
            return False

    # 写入temp.txt文件, 和读取对应
    def write_temp(self, contentDict):
        try:
            with open('./temp.txt', 'w', encoding='gbk') as f:
                for key, value in contentDict.items():
                    f.write(str(key) + '=' + str(value) + '\n')
        except Exception as e:
            print(e)

    # 初始化后运行的方法
    def login(self):
        hasCookies = self.get_cookies()
        # 获取登录页面
        if not (hasCookies and self.hasTemp):
            print('\n准备手动登录...')
            print('准备连接正方教务系统...')
            loginPage = self.get_page(self.loginUrl, self.headers)
            if (loginPage != None):
                isLink = 1 if findall(r'charset=(.*?)"',
                                      loginPage.text)[0] == self.charset else 0
                if isLink:
                    print('华南师范大学正方教务系统...连接成功')
                else:
                    input('请先连接校园网再重试，按任意键退出')
                    return None
                # 获取学号密码
                self.loginForm['txtUserName'] = input('请输入学号:')
                self.loginForm['TextBox2'] = input('请输入密码:')
                # 获取验证码
                self.loginForm['txtSecretCode'] = self.get_checkCode()
                # 获取隐藏属性
                self.loginForm['__VIEWSTATE'] = self.get_hiddenValue(loginPage)
                # 发送请求
                r = post(self.loginUrl,
                         data=self.loginForm,
                         headers=self.headers,
                         cookies=s.cookies,
                         verify=False)
                errorMsg = findall(r'alert\(\'(.*?)\'\)', r.text)
                if errorMsg != []:
                    print(errorMsg[0])
                    self.login()
                else:
                    print('登录成功，即将开始查询成绩...')
                    # 保存一下账号和姓名, 用于自动登录
                    writeContent = {}
                    writeContent['txtUserName'] = self.loginForm['txtUserName']
                    writeContent['xm'] = findall(r'id="xhxm">(.*?)同学<',
                                                 r.text)[0]
                    self.name = quote(writeContent['xm'].encode('gbk'))
                    # 更新一下self里的数据
                    self.scoreUrl = 'https://jwc.scnu.edu.cn/xscjcx.aspx?xh=' + str(
                        self.loginForm['txtUserName']
                    ) + '&xm=' + self.name + '&gnmkdm=N121605'
                    self.scoreHeaders['Referer'] = self.scoreUrl
                    self.write_temp(writeContent)
                    s.cookies.save(ignore_discard=True)
                    self.get_InternalHidden()
                    self.get_score()
            else:
                return None
        else:
            # 通过能不能获取隐藏属性来判断是否成功自动登录
            print('\n准备自动登录...')
            InternalVIEWSTATE = self.get_InternalHidden()
            if len(InternalVIEWSTATE) == 0:
                print('自动登录失败！')
                # 将hastemp取反, 来进行手动登录
                self.hasTemp = False
                self.login()
            else:
                print('自动登录成功，即将开始查询成绩...')
                self.get_score()

    # 将get请求抽取出来
    def get_page(self, url, headers):
        try:
            r = s.get(url, headers=headers, verify=False)
            if r.status_code == 200:
                return r
            else:
                print('请求失败!')
                return None
        except RequestException:
            print('网络请求失败')
            return None

    # 将post请求抽出来
    def postForm(self, url, headers, data):
        try:
            r = s.post(url, data=data, headers=headers)
            if r.status_code == 200:
                return r
            else:
                print('请求失败!')
                return None
        except RequestException:
            print('网络请求失败')
            return None

    # 获取验证码
    def get_checkCode(self):
        # 验证码路径
        r = self.get_page(
            self.checkCodeUrl,
            self.headers,
        )
        if r is None:
            raise RuntimeError('获取验证码失败，请检查网络或反馈')
        img = r.content
        # 将验证码写入本地
        local = open('checkCode.jpg', 'wb')
        local.write(img)
        local.close()
        print('正在打开验证码图片...')
        system('checkCode.jpg')
        checkCode = ''
        if input('是否需要切换一张验证码(y/n):').lower().strip() == 'y':
            checkCode = self.get_checkCode()
        else:
            checkCode = input('请输入验证码:')
        return checkCode

    # 获取VIEWSTATE隐藏属性, 用于提交表单(正方反爬策略之一)
    def get_hiddenValue(self, page):
        try:
            VIEWSTATE = findall(
                r'<input type="hidden" name="__VIEWSTATE" value="(.*?)" />',
                page.text)
        except Exception as e:
            return ['']
        return VIEWSTATE

    # cookiejar尝试接管cookie
    def get_cookies(self):
        try:
            s.cookies.load(ignore_discard=True)
            print('Cookie加载成功')
            return True
        except:
            print('Cookie未能加载')
            return False

    # 提取登录后页面的隐藏属性(很长的一串)(也算是反爬策略吧)
    def get_InternalHidden(self):
        if (self.InternalVIEWSTATE == ''):
            headers = {
                'user-agent':
                self.user_agent,
                'Host':
                self.host,
                'Referer':
                'https://jwc.scnu.edu.cn/xs_main.aspx?xh=' +
                str(self.loginForm['txtUserName'])
            }
            contentPage = self.get_page(self.scoreUrl, headers)
            self.InternalVIEWSTATE = self.get_hiddenValue(
                contentPage)[0].replace('\r', '').replace('\n', '')
            # 提取出来后更新一下self里的表单数据
            self.scoreForm['__VIEWSTATE'] = self.InternalVIEWSTATE
            return self.InternalVIEWSTATE
        else:
            return self.InternalVIEWSTATE

    # 获取成绩
    def get_score(self):
        self.scoreForm['ddlXN'] = input('请输入学年(格式如: 2018-2019):')
        self.scoreForm['ddlXQ'] = input('请输入学期(格式如: 1):')
        # 判断请求学期还是学年
        if self.scoreForm['ddlXQ'] == '1' or self.scoreForm[
                'ddlXQ'] == '2' or self.scoreForm['ddlXQ'] == '3':
            if 'btn_xn' in self.scoreForm:
                self.scoreForm.pop('btn_xn')
            self.scoreForm['btn_xq'] = u'学期成绩'.encode('gb2312')
        else:
            if 'btn_xq' in self.scoreForm:
                self.scoreForm.pop('btn_xq')
            self.scoreForm['btn_xn'] = u'学年成绩'.encode('gb2312')
        r = self.postForm(self.scoreUrl, self.scoreHeaders, self.scoreForm)
        # 将成绩table里的数据取出来然后print
        result = findall((r'<td>(.*?)</td>' * 19), r.text)
        print('\n查询结果为:\n')
        for items in result:
            temp = ''
            index = 0
            for item in items:
                # 跳过一些不需要的列
                if index in self.ignoreItem:
                    index = index + 1
                    continue
                # 清洗和调整结构, 方便print
                if item == '&nbsp;': item = '(空)'
                if search('</a>', item):
                    item = findall('>(.*?)</a>', item)[0]
                if len(item) > 8 and index > 0: item = item[:5] + '..'
                temp += item + '\t'
                index = index + 1
            print('%s\n' % temp)
        if input('\n查询结束，是否需要监听以上成绩(y/n):').lower().strip() == 'y':
            self.preNum = len(result)
            self.monitor_score()
        else:
            input('按任意键退出:')

    # 监听成绩的入口
    def monitor_score(self):
        if input('是否需要发送邮箱通知(y/n):').lower().strip() == 'y':
            if self.check_send_mail():
                self.needSend = True
                print('开始监听...\n当有新成绩时，将会在这里显示并发送新成绩到您设置的邮箱...')
                while True:
                    run_pending()
                    sleep(60)
        else:
            self.needSend = False
            print('开始监听...\n当有新成绩时，将会在这里显示...')
            while True:
                run_pending()
                sleep(60)

    # 确认目标邮箱
    def check_send_mail(self):
        aimMail = input('\n请输入要发送到的邮箱:')
        print('这是您输入的邮箱:', aimMail)
        if input('请确认输入是否正确，确认后将发送一封测试邮件到您邮箱(y/n):').lower().strip() == 'y':
            self.aimMail = aimMail
            if self.send_mail('测试邮件', '这是一封测试邮件'):
                print('发送测试邮件成功...')
                if input('是否成功收到邮件(y/n):').lower().strip() == 'n':
                    print('将重新发送测试邮件...')
                    return self.check_send_mail()
                else:
                    return True
            else:
                print('发送测试邮件失败!!!\n将重新发送测试邮件...')
                return self.check_send_mail()

    # 监听器, 这里使用schedule模块实现定时任务
    def monitor(self):
        r = self.postForm(self.scoreUrl, self.headers, self.scoreForm)
        result = findall((r'<td>(.*?)</td>' * 19), r.text)
        if len(result) < self.preNum:
            clear('monitor-score')
            raise BaseException('请求成绩失败! 请重新启动程序或反馈')
        if len(result) > self.preNum:
            # 检测到数量不一致,说明有新成绩
            self.preNum = len(result)
            if self.needSend:
                # 将成绩发送到邮箱
                content = findall(r'<div id="divNotPs">(.*?)</div>',
                                  r.text.replace('\r', '').replace('\n',
                                                                   ''))[0]
                if self.send_mail('您的正方教务系统有新成绩', content):
                    print('已将新成绩发送到指定邮箱')
                else:
                    print('新成绩发送邮箱失败！请重试或反馈')
            print('以下是新成绩:\n')
            for items in result:
                temp = ''
                index = 0
                for item in items:
                    # 跳过一些不需要的列
                    if index in self.ignoreItem:
                        index = index + 1
                        continue
                    # 清洗和调整结构, 方便print
                    if item == '&nbsp;': item = '(空)'
                    if search('</a>', item):
                        item = findall('>(.*?)</a>', item)[0]
                    if len(item) > 8 and index > 0: item = item[:5] + '..'
                    temp += item + '\t'
                    index = index + 1
                print('%s\n' % temp)

    # 发送邮件
    def send_mail(self, title, content):
        ret = True
        try:
            msg = MIMEText(content, 'html', self.charset)
            msg['From'] = formataddr(['工具人', self.sender])
            msg['To'] = formataddr(['aim', self.aimMail])
            msg['Subject'] = title
            server = SMTP_SSL('smtp.qq.com', 465)
            server.login(self.sender, self.MailPass)
            server.sendmail(self.sender, [
                self.aimMail,
            ], msg.as_string())
            server.quit()
        except Exception as e:
            print(e)
            ret = False
        return ret


if __name__ == '__main__':  # 命令行启动
    try:
        Spider = scoreSpider()  # 创建爬虫实例
        Spider.login()
    except KeyboardInterrupt as keye:
        pass
    except BaseException as e:
        print('异常 !!! ' + str(e))
        input('按任意键退出')
