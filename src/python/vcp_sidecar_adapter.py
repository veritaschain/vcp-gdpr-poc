#!/usr/bin/env python3
"""
VCP v1.1 Sidecar Adapter
========================

HTTP server that receives VCP events from MT5/cTrader and processes them
with crypto-shredding support for GDPR compliance.

Usage:
    python vcp_sidecar_adapter.py --port 8765

(C) 2025 VeritasChain Standards Organization
Licensed under Apache 2.0
"""

import argparse
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
import threading
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from python.vcp_crypto_shredding import VCPCryptoShredder, EventType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class VCPSidecarState:
    """Global state for the sidecar service"""
    
    def __init__(self):
        self.shredder = VCPCryptoShredder()
        self.events_received = 0
        self.events_processed = 0
        self.errors = 0
        self.start_time = datetime.utcnow()
        self.lock = threading.Lock()
    
    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            return {
                "status": "running",
                "uptime_seconds": uptime,
                "events_received": self.events_received,
                "events_processed": self.events_processed,
                "errors": self.errors,
                "chain_length": len(self.shredder.get_chain()),
                "version": "1.1.0"
            }


# Global state instance
state = VCPSidecarState()


class VCPSidecarHandler(BaseHTTPRequestHandler):
    """HTTP request handler for VCP Sidecar"""
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info("%s - %s", self.address_string(), format % args)
    
    def send_json_response(self, status: int, data: Dict[str, Any]):
        """Send a JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_json_response(200, {"status": "healthy"})
        
        elif self.path == '/stats':
            self.send_json_response(200, state.get_stats())
        
        elif self.path == '/chain':
            chain = state.shredder.get_chain()
            chain_data = [e.to_dict() for e in chain]
            self.send_json_response(200, {
                "chain_length": len(chain_data),
                "events": chain_data
            })
        
        elif self.path == '/chain/summary':
            self.send_json_response(200, state.shredder.get_chain_summary())
        
        elif self.path == '/verify':
            result = state.shredder.verify_chain_integrity()
            self.send_json_response(200, result)
        
        else:
            self.send_json_response(404, {"error": "Not found"})
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError as e:
            state.errors += 1
            self.send_json_response(400, {"error": f"Invalid JSON: {e}"})
            return
        
        state.events_received += 1
        
        if self.path == '/vcp/event':
            self._handle_event(data)
        
        elif self.path == '/vcp/erasure':
            self._handle_erasure(data)
        
        else:
            self.send_json_response(404, {"error": "Not found"})
    
    def _handle_event(self, data: Dict[str, Any]):
        """Process incoming VCP event"""
        try:
            gdpr_mode = data.get('gdpr_mode', False)
            pii_fields = data.get('pii_fields', [])
            event_data = data.get('event', data.get('payload', data))
            
            # Extract event type
            event_type_str = event_data.get('header', {}).get('event_type', 
                             event_data.get('event_type', 'ORD'))
            
            try:
                event_type = EventType[event_type_str]
            except KeyError:
                event_type = EventType.ORD
            
            # Extract payload
            payload = event_data.get('payload', event_data)
            
            # Determine subject ID
            subject_id = payload.get('account_id', 'UNKNOWN')
            if isinstance(subject_id, str) and subject_id.startswith('ENC:'):
                # Extract original value after the marker
                parts = subject_id.split(':')
                if len(parts) >= 3:
                    subject_id = parts[2]
            
            # Create VCP event with encryption
            vcp_event = state.shredder.create_event(
                event_type=event_type,
                payload=payload,
                pii_fields=pii_fields if gdpr_mode else [],
                subject_id=str(subject_id)
            )
            
            state.events_processed += 1
            
            logger.info(f"Processed {event_type.value} event: {vcp_event.header.event_id[:20]}...")
            
            self.send_json_response(200, {
                "status": "success",
                "event_id": vcp_event.header.event_id,
                "event_hash": vcp_event.header.event_hash,
                "gdpr_mode": gdpr_mode,
                "pii_encrypted": pii_fields
            })
            
        except Exception as e:
            state.errors += 1
            logger.error(f"Error processing event: {e}")
            self.send_json_response(500, {"error": str(e)})
    
    def _handle_erasure(self, data: Dict[str, Any]):
        """Process GDPR erasure request"""
        try:
            subject_id = data.get('subject_id')
            
            if not subject_id:
                self.send_json_response(400, {"error": "subject_id required"})
                return
            
            certificate = state.shredder.execute_erasure(subject_id)
            
            logger.info(f"Executed erasure for subject: {certificate.subject_id_hash[:20]}...")
            logger.info(f"Keys destroyed: {certificate.keys_destroyed}")
            
            self.send_json_response(200, {
                "status": "success",
                "certificate": certificate.to_dict()
            })
            
        except Exception as e:
            state.errors += 1
            logger.error(f"Error executing erasure: {e}")
            self.send_json_response(500, {"error": str(e)})


def run_server(port: int = 8765, host: str = '0.0.0.0'):
    """Run the VCP Sidecar server"""
    server = HTTPServer((host, port), VCPSidecarHandler)
    
    logger.info("=" * 60)
    logger.info("VCP v1.1 Sidecar Adapter")
    logger.info("GDPR-MiFID II Paradox Resolver")
    logger.info("=" * 60)
    logger.info(f"Server running on http://{host}:{port}")
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  GET  /health        - Health check")
    logger.info("  GET  /stats         - Server statistics")
    logger.info("  GET  /chain         - View event chain")
    logger.info("  GET  /chain/summary - Chain summary")
    logger.info("  GET  /verify        - Verify chain integrity")
    logger.info("  POST /vcp/event     - Submit VCP event")
    logger.info("  POST /vcp/erasure   - Execute GDPR erasure")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.shutdown()


def main():
    parser = argparse.ArgumentParser(
        description='VCP v1.1 Sidecar Adapter - GDPR-MiFID II Paradox Resolver'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8765,
        help='Port to listen on (default: 8765)'
    )
    parser.add_argument(
        '--host', '-H',
        type=str,
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    args = parser.parse_args()
    run_server(port=args.port, host=args.host)


if __name__ == '__main__':
    main()
