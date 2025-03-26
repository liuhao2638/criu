import time

def count():
    num = 0
    while True:
        print(num)
        num += 1
        time.sleep(1)  # 暂停一秒

if __name__ == "__main__":
    count()