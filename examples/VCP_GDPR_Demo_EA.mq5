//+------------------------------------------------------------------+
//| VCP_GDPR_Demo_EA.mq5                                              |
//| Example EA demonstrating VCP v1.1 GDPR-compliant logging          |
//|                                                                    |
//| (C) 2025 VeritasChain Standards Organization                      |
//+------------------------------------------------------------------+
#property copyright "VeritasChain Standards Organization"
#property link      "https://veritaschain.org"
#property version   "1.10"
#property strict
#property description "Demo EA for VCP v1.1 Crypto-Shredding"
#property description "Generates GDPR-compliant audit trail"

//+------------------------------------------------------------------+
//| Include VCP GDPR Bridge                                           |
//+------------------------------------------------------------------+
#include <VCP/vcp_gdpr_bridge.mqh>

//+------------------------------------------------------------------+
//| Input Parameters                                                  |
//+------------------------------------------------------------------+
input string   InpAlgorithmId     = "VCP-DEMO-001";        // Algorithm ID
input string   InpAlgorithmVersion = "1.0.0";              // Algorithm Version
input string   InpSidecarUrl      = "http://localhost:8765/vcp/event"; // Sidecar URL
input double   InpLotSize         = 0.01;                  // Lot Size
input int      InpMagicNumber     = 12345;                 // Magic Number
input bool     InpEnableLogging   = true;                  // Enable VCP Logging

//+------------------------------------------------------------------+
//| Global Variables                                                  |
//+------------------------------------------------------------------+
CVCPGDPRBridge g_vcpBridge;
int g_orderTicket = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("================================================");
   Print("VCP v1.1 GDPR-Compliant Demo EA");
   Print("Solving the GDPR-MiFID II Paradox");
   Print("================================================");
   
   // Initialize VCP Bridge
   if(InpEnableLogging)
   {
      if(!g_vcpBridge.Init(InpAlgorithmId, InpAlgorithmVersion, InpSidecarUrl))
      {
         Print("[ERROR] Failed to initialize VCP Bridge");
         return INIT_FAILED;
      }
      
      Print("[VCP] GDPR-compliant logging ENABLED");
      Print("[VCP] PII fields will be encrypted automatically");
   }
   else
   {
      Print("[VCP] Logging DISABLED");
   }
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("[VCP] Demo EA stopped. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Simple demo logic: Place order on first tick if none exists
   if(g_orderTicket == 0 && PositionsTotal() == 0)
   {
      // Create VCP event BEFORE placing order
      VCPTradeEvent orderEvent;
      
      if(InpEnableLogging)
      {
         string decisionFactors = "DEMO_FIRST_TICK,RSI=" + 
                                  DoubleToString(CalculateDemoRSI(), 2);
         
         if(g_vcpBridge.CreateOrderEvent(orderEvent, 
                                          Symbol(), 
                                          ORDER_TYPE_BUY, 
                                          InpLotSize, 
                                          SymbolInfoDouble(Symbol(), SYMBOL_ASK),
                                          0, 0,  // SL/TP
                                          decisionFactors))
         {
            Print("[VCP] Order event created: ", orderEvent.header.event_id);
            Print("[VCP] PII encrypted: account_id, client_ip");
            
            // Send to sidecar
            g_vcpBridge.SendToSidecar(orderEvent);
         }
      }
      
      // Place the actual order
      MqlTradeRequest request = {};
      MqlTradeResult result = {};
      
      request.action = TRADE_ACTION_DEAL;
      request.symbol = Symbol();
      request.volume = InpLotSize;
      request.type = ORDER_TYPE_BUY;
      request.price = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
      request.deviation = 10;
      request.magic = InpMagicNumber;
      request.comment = "VCP Demo - " + orderEvent.header.event_id;
      
      if(OrderSend(request, result))
      {
         g_orderTicket = (int)result.order;
         Print("[TRADE] Order placed: ", g_orderTicket);
         
         // Create ACK event
         if(InpEnableLogging)
         {
            VCPTradeEvent ackEvent;
            if(g_vcpBridge.CreateAckEvent(ackEvent, 
                                           orderEvent.header.event_id,
                                           "MT5-DEMO",
                                           true))  // accepted
            {
               Print("[VCP] ACK event created: ", ackEvent.header.event_id);
               g_vcpBridge.SendToSidecar(ackEvent);
            }
         }
      }
      else
      {
         Print("[TRADE] Order failed: ", result.retcode);
         
         // Create REJ event
         if(InpEnableLogging)
         {
            VCPTradeEvent rejEvent;
            if(g_vcpBridge.CreateAckEvent(rejEvent,
                                           orderEvent.header.event_id,
                                           "MT5-DEMO",
                                           false))  // rejected
            {
               Print("[VCP] REJ event created: ", rejEvent.header.event_id);
               g_vcpBridge.SendToSidecar(rejEvent);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Trade transaction handler                                         |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
{
   // Log execution events
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD && InpEnableLogging)
   {
      VCPTradeEvent exeEvent;
      
      if(g_vcpBridge.CreateExecutionEvent(exeEvent,
                                           "ORD-" + IntegerToString(trans.order),
                                           "EXE-" + IntegerToString(trans.deal),
                                           trans.price,
                                           trans.volume))
      {
         Print("[VCP] EXE event created: ", exeEvent.header.event_id);
         Print("[VCP] Fill: ", trans.volume, " @ ", trans.price);
         g_vcpBridge.SendToSidecar(exeEvent);
      }
   }
}

//+------------------------------------------------------------------+
//| Demo RSI calculation (placeholder)                                |
//+------------------------------------------------------------------+
double CalculateDemoRSI()
{
   // Simplified demo - return random value between 30-70
   return 30.0 + (MathRand() % 41);
}

//+------------------------------------------------------------------+
//| Demo: Request GDPR erasure (call from script or button)           |
//+------------------------------------------------------------------+
void RequestGDPRErasure()
{
   if(!InpEnableLogging)
   {
      Print("[VCP] Logging not enabled, cannot request erasure");
      return;
   }
   
   VCPErasureCertificate certificate;
   
   // Use account login as subject ID
   string subjectId = "TRADER-" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
   
   if(g_vcpBridge.RequestErasure(certificate, subjectId))
   {
      Print("================================================");
      Print("[VCP] GDPR ERASURE EXECUTED");
      Print("================================================");
      Print("[VCP] Certificate ID: ", certificate.certificate_id);
      Print("[VCP] Subject Hash: ", certificate.subject_id_hash);
      Print("[VCP] Keys Destroyed: ", certificate.keys_destroyed);
      Print("[VCP] Method: ", certificate.method);
      Print("[VCP] Hash Chain Intact: ", certificate.hash_chain_intact);
      Print("[VCP] PII Recoverable: ", certificate.pii_recoverable);
      Print("[VCP] Audit Trail Preserved: ", certificate.audit_trail_preserved);
      Print("================================================");
      Print("[VCP] GDPR-MiFID II PARADOX RESOLVED!");
      Print("================================================");
   }
}

//+------------------------------------------------------------------+
//| Chart event handler (for UI interaction)                          |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
   // Handle button click for GDPR erasure demo
   if(id == CHARTEVENT_OBJECT_CLICK && sparam == "btnGDPRErasure")
   {
      RequestGDPRErasure();
   }
}
//+------------------------------------------------------------------+
