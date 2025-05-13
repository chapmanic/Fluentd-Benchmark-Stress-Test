########################################################################################################################
# Fluentd Dummy log generator
#
# Default args can be hard coded into the script, if no kwargs provided, these will be used.
# Allows duration in seconds, rate of logs (per sec), size of log entry in bytes, host, port and log tag
#
# ~~ EXAMPLE USAGE ~~
# RUN: py fluentd-benchmark.py --seconds 10 --rate 10 --size 848 --host fluentd.domain.com --port 24224 --tag ops-test
# OR:  py fluentd-benchmark.py 60 --rate 100 --size 2000
#
########################################################################################################################


#################################################
#
# Imports
#
##################################################

import argparse
import time
import socket
from fluent import sender
import json, random, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

#################################################
#
# Function to send logs to Fluentd
#
# Instantiates its own FluentSender
# Returns True on success, False on error
# short timeout and ensures proper socket closure
#
##################################################

def send_log(tag, data, host, port):
    """Worker thread: build its own FluentSender, return True on success."""
    thread_logger = sender.FluentSender('', host=host, port=port, timeout=3.0)
    try:
        return thread_logger.emit(tag, data)
    except Exception as e:
        print(f"[send_log] Error: {e}")
        return False
    finally:
        thread_logger.close()

#################################################
#
# Function to generate Rand log entry
#
# Generates a random log w/ payload size arg
#
##################################################

def generate_log_entry(index, target_size_bytes=848, report_size=False):
    levels   = ['INFO', 'DEBUG', 'WARN', 'ERROR']
    services = ['auth-service', 'billing-service', 'user-service',
                'inventory', 'notifications']

    base = {
        "log_id"   : str(uuid.uuid4()),
        "level"    : random.choice(levels),
        "service"  : random.choice(services),
        "user_id"  : random.randint(1000, 9999),
        "message"  : f"Log event {index} - simulated operation completed.",
        "host"     : socket.gethostname(),
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "trace_id" : str(uuid.uuid4())[:16],
        "session_id": str(uuid.uuid4())[:16],
    }

    cur_size = len(json.dumps(base).encode())
    pad_len  = max(target_size_bytes - cur_size - len('"payload":""') - 2, 0)
    base["payload"] = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=pad_len))

    if report_size:
        print(f"[Log {index}] log size: {len(json.dumps(base).encode())} bytes")
    return base

#################################################
#
# Main function to run the load test
#
# Timer tracking total runtime w/ reachable check
#
##################################################

def main(duration, host, port, tag_prefix, rate, size):
    print(f"Connecting to Fluentd {host}:{port}  tag_prefix={tag_prefix}")
    quick_check = sender.FluentSender('', host=host, port=port, timeout=3.0)
    if not quick_check.emit('connection_test', {'msg': 'ping'}):
        print("Initial connection test failed - exiting.")
        return
    quick_check.close()

    tag = f"INFO.{tag_prefix}.dev.unspecified"
    print(f"Sending {rate} logs/sec for {duration} seconds…\n")

    success_count = 0
    error_count   = 0
    total_to_send = duration * rate
    start_ts      = time.time()

    for second in range(duration):
        second_start = time.time()

        with ThreadPoolExecutor(max_workers=min(rate, 500)) as pool:
            futs = []
            for i in range(rate):
                idx   = second * rate + i + 1
                first = (second == 0 and i == 0)
                data  = generate_log_entry(idx, size, report_size=first)
                futs.append(pool.submit(send_log, tag, data, host, port))

            for fut in as_completed(futs):
                if fut.result():
                    success_count += 1
                else:
                    error_count += 1

        elapsed = time.time() - second_start
        print(f"  • second {second+1:2}/{duration}: {rate} logs in {elapsed:.2f}s")

        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)

    total_time = time.time() - start_ts
    print("\n=====  Run complete  =====")
    print(f" attempted : {total_to_send:,}")
    print(f" succeeded : {success_count:,}")
    print(f" failed    : {error_count:,}")
    print(f" success % : {success_count / total_to_send * 100:5.2f}%")
    print(f" elapsed   : {total_time:.2f}s\n")

#################################################
#
# Ensure CLI is run as main program
#
##################################################

if __name__ == "__main__":
    p = argparse.ArgumentParser("Fluentd load-benchmark")
    p.add_argument('seconds', type=int, help="Duration of test")
    p.add_argument('--rate', type=int, default=10, help="Logs per second")
    p.add_argument('--size', type=int, default=848, help="Approximate log size")
    p.add_argument('--host', default='localhost')
    p.add_argument('--port', type=int, default=24224)
    p.add_argument('--tag',  default='ops-test')
    a = p.parse_args()

    main(a.seconds, a.host, a.port, a.tag, a.rate, a.size)