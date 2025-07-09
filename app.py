import asyncio
import sys
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from collections import deque

# Assuming these are available from your original setup
from utils import get_config_dir, get_client, print_progress 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here' 

socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

progress_queue = deque(maxlen=20) # Keep a history of the last 20 progress updates

monitoring_active = False
monitoring_thread = None 

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')

@socketio.on('connect')
def test_connect(auth=None): # Added auth=None to avoid TypeError
    """Handle new WebSocket connections."""
    global monitoring_active
    print('Client connected')
    
    if progress_queue:
        # When a new client connects, send them the latest available progress
        # We send the *list* of the deque, so the frontend can build its history
        emit('progress_update', list(progress_queue)) 
    
    if not monitoring_active:
        start_monitoring()

@socketio.on('disconnect')
def test_disconnect():
    """Handle WebSocket disconnections."""
    print('Client disconnected')

def start_monitoring():
    """Starts the background task to monitor progress."""
    global monitoring_active, monitoring_thread
    if not monitoring_active:
        monitoring_active = True
        monitoring_thread = threading.Thread(target=run_monitor_loop, daemon=True)
        monitoring_thread.start()
        print("Monitoring task started in a new thread.")

def run_monitor_loop():
    """Runs the asyncio event loop for the monitor_eas_progress coroutine."""
    global monitoring_active
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    config_dir = get_config_dir(sys.argv)
    local_eas_client = get_client(config_dir)
    
    try:
        loop.run_until_complete(monitor_eas_progress(local_eas_client))
    except Exception as e:
        print(f"Error running monitor loop: {e}")
    finally:
        if local_eas_client:
            # Ensure aclose is awaited on the correct loop
            asyncio.run_coroutine_threadsafe(local_eas_client.aclose(), loop)
            print("EAS client closed in monitoring thread.")
        loop.close()
        print("Monitor loop closed.")

async def monitor_eas_progress(eas_client_instance):
    """
    Asynchronously monitors the EAS client for progress updates
    and emits them via WebSocket.
    """
    global monitoring_active
    try:
        while monitoring_active:
            result = await eas_client_instance.async_get_hosting_capacity_work_packages_progress()
            progress_queue.append(result)
            
            # Emit just the latest result to all clients
            socketio.emit('progress_update', result) 
            print(f"Emitted progress: {result}") 
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        print("EAS progress monitoring task was cancelled.")
    except Exception as e:
        print(f"Error in monitor_eas_progress: {e}")
    finally:
        monitoring_active = False 
        print("Monitoring task finished.")

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)