import os
import json
import Bybitlite as bb

# main account
APIid = {'key': os.environ.get('BYBIT_KEY'), 'secret': os.environ.get('BYBIT_SECRET')}
# sub account list
APIids = json.loads(os.environ.get('PIPER_KEYS'))
bb.set_id(APIid['key'], APIid['secret'], 'https://api.bybit.com')

def pipeorders():
    avgprice = 0
    totalqty = 0
    weight = 0

    # read all untriggered orders from main account
    orderlist = bb.conditionalorderslist('BTCUSD', stop_order_status='Untriggered')

    # let's calculate the predicted average price in case all orders are triggered
    for order in orderlist:
        totalqty += int(order['qty'])
        weight += float(order['price'])*float(order['qty'])
        avgprice = weight/totalqty

    # activate main account and extract valuable data
    myposition = bb.position()
    lastprice = bb.tickers('BTCUSD')[0]['last_price']
    mybalance = myposition['wallet_balance']
    myleverage = myposition['leverage']
    mypnl = myposition['unrealised_pnl']
    worstprice = avgprice * (1 - 1 / (float(myleverage) + 1))
    myqty = float(lastprice) * float(mybalance) * float(myleverage)
    print(f'\nMain account data:\n    quantity: {myqty}\n    balance: {mybalance}\n    leverage: {myleverage}'
          f'\n    pnl: {mypnl:10.8f}BTC\n    {mypnl*float(lastprice):10.2f}$')

    # activate sub accounts and extract valuable data
    for APIid in APIids:
        bb.set_id(APIid['key'], APIid['secret'])
        print(f'\nAccount name: {APIid["name"]}')
        position = bb.position()
        balance = position['wallet_balance']
        leverage = position['leverage']
        pnl = position['unrealised_pnl']
        qty = float(lastprice) * float(balance) * float(leverage) * 0.97
        print(f'    quantity: {qty}\n    balance: {balance}\n    leverage: {leverage}'
              f'\n    pnl: {pnl:10.8f}BTC\n   {pnl*float(lastprice):10.2f}$')
        bb.cancelallconditionals('BTCUSD')
        print(f'\n order report:')

        # copy the order list into active sub account
        for index, order in enumerate(orderlist):
            totalqty += int(order['qty'])
            weight += float(order['price']) * float(order['qty'])
            adjfactor = float(order['qty'])/myqty
            newqty = int(adjfactor * qty)
            print(f'  {index + 1}  {order["price"]}  {order["side"]}  {int(order["qty"])} - {newqty}')
            bb.conditionalorder(order['side'], order['symbol'], order['order_type'], newqty,
                                order['base_price'], order['stop_px'], price=order['price'])
            
    # print common price data
    print(f'\nLast price: {lastprice}\npredicted avg price: {avgprice}\nworst case price: {worstprice}')


pipeorders()
