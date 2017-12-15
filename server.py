import requests

if __name__ == '__main__':
    r = requests.get('http://www.baidu.com')
    print r.text