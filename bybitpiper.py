import os
import json
import Bybitlite as bb

APIid = {'key': os.environ.get('BYBIT_KEY'), 'secret': os.environ.get('BYBIT_SECRET')}
APIids = json.loads(os.environ.get('PIPER_KEYS'))
bb.set_id(APIid['key'], APIid['secret'], 'https://api.bybit.com')

def copyorders():
    avgprice = 0
    totalqty = 0
    weight = 0
    # read and copy untriggered orders from main account
    orderlist = bb.conditionalorderslist('BTCUSD', stop_order_status='Untriggered')

    #let's claculate the average price
    for order in orderlist:
        totalqty += int(order['qty'])
        weight += float(order['price'])*float(order['qty'])
        avgprice = weight/totalqty

    myposition = bb.position()
    lastprice = bb.tickers('BTCUSD')[0]['last_price']
    mybalance = myposition['wallet_balance']
    myleverage = myposition['leverage']
    myqty = float(lastprice) * float(mybalance) * float(myleverage)
    print(f'\nMain account data:\n       qty: {myqty}\n   balance: {mybalance}\n  leverage: {myleverage}')

    for APIid in APIids:
        bb.set_id(APIid['key'], APIid['secret'])
        print(f'\nAccount name: {APIid["name"]}')
        position = bb.position()
        balance = position['wallet_balance']
        leverage = position['leverage']
        qty = float(lastprice) * float(balance) * float(leverage) * 0.97
        print(f'  balance: {balance}\n  leverage: {leverage}\n  quantity: {qty}')
        bb.cancelallconditionals('BTCUSD')
        worstprice = avgprice * (1 - 1 / (float(leverage) + 1))
        print(f'\npiper report:')

        for index, order in enumerate(orderlist):
            totalqty += int(order['qty'])
            weight += float(order['price']) * float(order['qty'])
            adjfactor = float(order['qty'])/myqty
            newqty = int(adjfactor * qty)
            print(f'  {index + 1}  {order["price"]}  {order["side"]}  {int(order["qty"])} - {newqty}')
            bb.conditionalorder(order['side'], order['symbol'], order['order_type'], newqty,
                                order['base_price'], order['stop_px'], price=order['price'])

    print(f'\npredicted avg price: {avgprice}\nworst case price: {worstprice}')


copyorders()
