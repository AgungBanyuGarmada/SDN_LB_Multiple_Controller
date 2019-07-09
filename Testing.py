import pexpect
import time
import pika
import json
import threading
import MySQLdb

db = MySQLdb.connect("localhost", "root", "", "Skripsi")
cursor = db.cursor()

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    time.sleep(body.count(b'.'))
    ch.basic_ack(delivery_tag = method.delivery_tag)
    a = json.loads(body)
    pxpct.sendline("py net.get('switch" + a["Switch_id"][16] + "').start(["+a["Controller_id"]+"])")
    pxpct.expect('mininet>')

    # connectdb()
    # cursor = db.cursor()
    sql = ('update sdn_link set c_name = %s where s_name = %s')
    cursor.execute(sql, (a["Controller_id"], a["Switch_id"]))
    db.commit()
    # disconnectdb()
    # cursor.close()

def init_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='queue_3', durable=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(callback,queue='queue_3')
    channel.start_consuming()


def connectdb():
    global db
    db = MySQLdb.connect("localhost", "root", "", "Skripsi")


def disconnectdb():
    global db
    db.close()
    db = None

if __name__=="__main__":
    # connectdb()
    # cursor = db.cursor()

    sql = ('update sdn_link set c_name = %s where s_name = %s')

    threading._start_new_thread(init_rabbitmq, ())
    global pxpct
    pxpct = pexpect.spawn('python',['TAv1.py'])

    pxpct.expect('mininet>')
    pxpct.sendline("py net.get('switch1').start([poxController])")
    cursor.execute(sql, ('poxController','00-00-00-00-00-01'))

    pxpct.expect('mininet>')
    pxpct.sendline("py net.get('switch2').start([poxController])")
    cursor.execute(sql, ('poxController', '00-00-00-00-00-02'))

    pxpct.expect('mininet>')
    pxpct.sendline("py net.get('switch3').start([poxController])")
    cursor.execute(sql, ('poxController', '00-00-00-00-00-03'))

    pxpct.expect('mininet>')
    pxpct.sendline("py net.get('switch4').start([poxController])")
    cursor.execute(sql, ('poxController', '00-00-00-00-00-04'))

    pxpct.expect('mininet>')
    pxpct.sendline("py net.get('switch5').start([poxController2])")
    cursor.execute(sql, ('poxController2', '00-00-00-00-00-05'))

    pxpct.expect('mininet>')
    pxpct.sendline("py net.get('switch6').start([poxController2])")
    cursor.execute(sql, ('poxController2', '00-00-00-00-00-06'))

    pxpct.expect('mininet>')
    pxpct.sendline("py net.get('switch7').start([poxController2])")
    cursor.execute(sql, ('poxController2', '00-00-00-00-00-07'))

    pxpct.expect('mininet>')
    pxpct.sendline("py net.get('switch8').start([poxController2])")
    cursor.execute(sql, ('poxController2', '00-00-00-00-00-08'))

    pxpct.expect('mininet>')
    pxpct.sendline('xterm h1 h2 h5 h6')
    pxpct.expect('mininet>')

    db.commit()
    # disconnectdb()
    # cursor.close()

    while True:
        pass
    # x.sendline('net')
    # x.expect('mininet>')
    # pxpct.sendline('exit')
