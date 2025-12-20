from flask import Flask, request, jsonify
import time
import random
import hashlib
from datetime import datetime

app = Flask(__name__)

# In-memory storage (in production, use a database)
withdrawals_db = []
auto_withdrawals = {}
gas_prices = {
    'slow': {'price': 20, 'time': '30-60 min'},
    'medium': {'price': 30, 'time': '5-15 min'},
    'fast': {'price': 50, 'time': '1-3 min'}
}

@app.route('/api/withdrawal/initiate', methods=['POST'])
def initiate_withdrawal():
    data = request.json
    
    # Validate request
    required_fields = ['wallet_address', 'amount', 'currency', 'mode']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    wallet = data['wallet_address']
    amount = float(data['amount'])
    currency = data['currency']
    mode = data['mode']
    
    # Validate wallet address (basic check)
    if not wallet.startswith('0x') or len(wallet) < 42:
        return jsonify({'error': 'Invalid wallet address format'}), 400
    
    # Validate amount
    if amount < 10:
        return jsonify({'error': 'Minimum withdrawal is $10'}), 400
    
    # Generate transaction ID
    tx_id = hashlib.sha256(f"{wallet}{amount}{time.time()}".encode()).hexdigest()[:64]
    
    # Create withdrawal record
    withdrawal = {
        'id': tx_id,
        'wallet': wallet,
        'amount': amount,
        'currency': currency,
        'mode': mode,
        'status': 'pending',
        'timestamp': datetime.now().isoformat(),
        'gas_price': data.get('gas_price', 30),
        'estimated_fee': calculate_fee(amount, data.get('gas_price', 30))
    }
    
    withdrawals_db.append(withdrawal)
    
    # Simulate blockchain transaction (in real app, this would call Web3)
    simulate_transaction_processing(withdrawal)
    
    return jsonify({
        'success': True,
        'message': 'Withdrawal initiated',
        'transaction_id': tx_id,
        'estimated_confirmation': '1-3 confirmations',
        'fee': withdrawal['estimated_fee']
    })

@app.route('/api/withdrawal/auto/enable', methods=['POST'])
def enable_auto_withdrawal():
    data = request.json
    
    required_fields = ['wallet_address', 'threshold', 'currency']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    user_id = data.get('user_id', 'default_user')
    
    auto_withdrawals[user_id] = {
        'wallet': data['wallet_address'],
        'threshold': float(data['threshold']),
        'currency': data['currency'],
        'frequency': data.get('frequency', 'instant'),
        'enabled': True,
        'last_check': datetime.now().isoformat()
    }
    
    return jsonify({
        'success': True,
        'message': 'Auto-withdrawal enabled',
        'settings': auto_withdrawals[user_id]
    })

@app.route('/api/withdrawal/auto/disable', methods=['POST'])
def disable_auto_withdrawal():
    data = request.json
    user_id = data.get('user_id', 'default_user')
    
    if user_id in auto_withdrawals:
        auto_withdrawals[user_id]['enabled'] = False
    
    return jsonify({'success': True, 'message': 'Auto-withdrawal disabled'})

@app.route('/api/withdrawal/history', methods=['GET'])
def get_withdrawal_history():
    user_id = request.args.get('user_id', 'default_user')
    
    # Filter withdrawals (in production, would query by user_id)
    user_withdrawals = [w for w in withdrawals_db if w.get('user_id', 'default_user') == user_id]
    
    return jsonify({
        'success': True,
        'withdrawals': user_withdrawals[-10:],  # Last 10 withdrawals
        'total_count': len(user_withdrawals)
    })

@app.route('/api/withdrawal/status/<tx_id>', methods=['GET'])
def get_withdrawal_status(tx_id):
    withdrawal = next((w for w in withdrawals_db if w['id'] == tx_id), None)
    
    if not withdrawal:
        return jsonify({'error': 'Transaction not found'}), 404
    
    # Simulate progress
    if withdrawal['status'] == 'pending':
        # Randomly confirm some transactions
        if random.random() > 0.7:
            withdrawal['status'] = 'confirmed'
            withdrawal['confirmed_at'] = datetime.now().isoformat()
            withdrawal['confirmations'] = random.randint(3, 12)
    
    return jsonify({
        'success': True,
        'transaction': withdrawal
    })

@app.route('/api/gas/estimate', methods=['POST'])
def estimate_gas():
    data = request.json
    amount = float(data.get('amount', 0))
    priority = data.get('priority', 'medium')
    
    gas_info = gas_prices.get(priority, gas_prices['medium'])
    fee = calculate_fee(amount, gas_info['price'])
    
    return jsonify({
        'success': True,
        'gas_price': gas_info['price'],
        'estimated_fee': fee,
        'completion_time': gas_info['time'],
        'priority': priority
    })

@app.route('/api/withdrawal/limits', methods=['GET'])
def get_limits():
    return jsonify({
        'success': True,
        'limits': {
            'daily': 10000,
            'monthly': 100000,
            'minimum': 10,
            'maximum': 50000
        },
        'fees': {
            'percentage': 0.001,
            'minimum_fee': 5,
            'network_fee': 'variable'
        }
    })

def calculate_fee(amount, gas_price):
    # 0.1% fee, minimum $5
    fee = amount * 0.001
    return max(5, round(fee, 2))

def simulate_transaction_processing(withdrawal):
    # Simulate async processing
    import threading
    
    def process():
        time.sleep(random.uniform(2, 5))  # Simulate processing time
        withdrawal['status'] = 'processing'
        
        time.sleep(random.uniform(10, 30))  # Simulate blockchain confirmation
        withdrawal['status'] = 'confirmed'
        withdrawal['confirmations'] = random.randint(3, 12)
        withdrawal['confirmed_at'] = datetime.now().isoformat()
    
    thread = threading.Thread(target=process)
    thread.daemon = True
    thread.start()

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'AINEON Withdrawal API',
        'timestamp': datetime.now().isoformat(),
        'endpoints': [
            '/api/withdrawal/initiate',
            '/api/withdrawal/auto/enable',
            '/api/withdrawal/history',
            '/api/withdrawal/status/<tx_id>',
            '/api/gas/estimate',
            '/api/withdrawal/limits'
        ]
    })

if __name__ == '__main__':
    print("íº€ AINEON Withdrawal API Starting...")
    print("âœ… Endpoints:")
    print("   â€¢ POST   /api/withdrawal/initiate")
    print("   â€¢ POST   /api/withdrawal/auto/enable")
    print("   â€¢ GET    /api/withdrawal/history")
    print("   â€¢ GET    /api/withdrawal/status/<tx_id>")
    print("   â€¢ POST   /api/gas/estimate")
    print("   â€¢ GET    /api/withdrawal/limits")
    print("\ní³Š Dashboard: Open dashboard-with-withdrawal.html")
    app.run(host='0.0.0.0', port=8081, debug=True)
