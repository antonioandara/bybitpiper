import os
import json
import Bybitlite as bb


# API keys are stored as environment variables
# main account
APIid = {'key': os.environ.get('BYBIT_KEY'),
         'secret': os.environ.get('BYBIT_SECRET'), 'name': 'main'}
# sub account list
APIids = json.loads(os.environ.get('PIPER_KEYS'))
# APIids = [{'key': os.environ.get('BYBIT_TESTNET_KEY'),
#            'secret': os.environ.get('BYBIT_TESTNET_SECRET'),
#            'name': 'test'}]

# this set will contain all the orders synced from the main account to the sub accounts
syncedorders = {}


def pipeorders(pipe=True):
    global APIid
    global APIids
    with open('order_index.txt') as json_file:
        syncedorders = json.load(json_file)

    # read all untriggered orders from main account
    orderindex, orderlist, mainbalance = readaccount(APIid)
    lastprice = bb.tickers('BTCUSD')[0]['last_price']

    # activate sub accounts and extract valuable data
    for api in APIids:
        if api['name'] == 'test':
            bb.set_id(api['key'], api['secret'], 'https://api-testnet.bybit.com')
        else:
            bb.set_id(api['key'], api['secret'])
        # if the sub account doesn't have any synced orders an empty dic will be created
        if not api['name'] in syncedorders:
            syncedorders[api['name']] = {}
        # this list represents the ids from the main account orders
        suborderlist = set(syncedorders[api['name']].keys())

        # let's check for orders that were cancelled since the last time we synced the accounts
        for suborder in suborderlist:
            if suborder not in orderindex:
                cancelled = bb.cancelconditional('BTCUSD', stop_order_id=syncedorders[api["name"]][suborder]["stop_order_id"])
                syncedorders[api["name"]].pop(suborder)

        suborderindex, suborderlist, subbalance = readaccount(api)

        # sync main order list into sub account
        print(f'    ---- Order report -----')

        for index, order in enumerate(orderlist):
            qty = int(float(order['adj_factor']) * float(subbalance))
            print(f'  {index + 1}  {order["price"]}  {order["side"]}  {int(order["qty"])} - {qty}', end=" ")

            if pipe:
                if order['stop_order_id'] in syncedorders[api['name']].keys():
                    print(f'{order["stop_order_id"]} already synced as '
                          f'{syncedorders[api["name"]][order["stop_order_id"]]["stop_order_id"]}')
                else:
                    syncedorders[api['name']][order['stop_order_id']] =\
                        bb.conditionalorder(order['side'], order['symbol'], order['order_type'],
                                            qty, order['base_price'], order['stop_px'], price=order['price'])
                    print(f'just synced as {syncedorders[api["name"]][order["stop_order_id"]]["stop_order_id"]}')
            else:
                if order['stop_order_id'] in syncedorders[api['name']].keys():
                    print(f'{order["stop_order_id"]} already synced as '
                          f'{syncedorders[api["name"]][order["stop_order_id"]]["stop_order_id"]}')
                else:
                    print(f'{order["stop_order_id"]} not synced')

    with open('order_index.txt', 'w') as file:  # Use file to refer to the file object
        file.write(json.dumps(syncedorders))
    return syncedorders


def readaccount(APIid, symbol='BTCUSD'):
    totalqty = 0
    weight = 0
    orderindex = set()
    bb.set_id(APIid['key'], APIid['secret'], 'https://api.bybit.com')

    # extract valuable data from main account
    position = bb.position()
    # print(position)
    size = position['size']
    lastprice = bb.tickers('BTCUSD')[0]['last_price']
    balance = position['wallet_balance']
    leverage = position['leverage']
    pnl = position['unrealised_pnl']
    qty = float(lastprice) * float(balance) * float(leverage)
    orderlist = bb.conditionalorderslist(symbol, stop_order_status='Untriggered')
    untrintriggered = len(orderlist)

    # let's calculate the predicted average price in case all orders are triggered
    for order in orderlist:
        orderindex.add(order['stop_order_id'])
        totalqty += int(order['qty'])
        weight += float(order['price']) * float(order['qty'])
        order['adj_factor'] = float(order['qty']) / float(balance)

    avgprice = (weight + float(size) * float(position['entry_price'])) / (totalqty + size)
    worstprice = avgprice * (1 - 1 / (float(leverage) + 1))
    print(f'\nAccount {APIid["name"]}:\n'
          f'    untriggered: {untrintriggered}\n'
          f'    quantity:    {qty:.0f}\n'
          f'    balance:     {balance}\n'
          f'    leverage:    {leverage}\n'
          f'    size:        {size}\n'
          f'    pnl:         {pnl:10.8f}BTC\n'
          f'            {pnl * float(lastprice):10.2f}$\n'
          f'    avg price:   {avgprice:10.0f}\n'
          f'    worst price: {worstprice:10.0f}\n')
    return orderindex, orderlist, balance


def canceall(APIids):
    for api in APIids:
        print(f'cancelling orders from account: {api["name"]}')
        bb.set_id(api['key'], api['secret'], 'https://api.bybit.com')
        bb.cancelallconditionals('BTCUSD')

# to initialize
# lastsync = {}
# with open('order_index.txt', 'w') as file:  # Use file to refer to the file object
#     file.write(json.dumps(lastsync))
# canceall(APIids)

pipeorders(True)
