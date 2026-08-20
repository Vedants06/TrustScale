"use client";

import { useEffect, useState, useRef } from "react";
import {
  Train,
  CheckCircle2,
  XCircle,
  Clock,
  Server,
  Ticket,
  Play,
  Square,
  Activity
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useActivityLog } from "@/lib/hooks/useActivityLog";
import type { TrainInfo, BookingResult } from "@/lib/types";

const PASSENGER_NAMES = [
  "Rahul Kumar",
  "Priya Sharma",
  "Amit Patel",
  "Sneha Gupta",
  "Vijay Singh",
  "Anita Desai",
  "Rohit Verma",
  "Kavita Reddy",
  "Suresh Nair",
  "Meera Joshi",
  "Arjun Singh",
  "Neha Kapur"
];

const SEAT_CLASSES = ["SL", "3A", "2A", "1A"];

export function BookingDemo() {
  const [trains, setTrains] = useState<TrainInfo[]>([]);
  const [selectedTrain, setSelectedTrain] = useState<string>("");
  const [selectedClass, setSelectedClass] = useState<string>("3A");
  
  // UI States
  const [isBooking, setIsBooking] = useState(false);
  const [isBulkBooking, setIsBulkBooking] = useState(false);
  const [isContinuousLoad, setIsContinuousLoad] = useState(false);
  
  // Stats & History
  const [bookingHistory, setBookingHistory] = useState<BookingResult[]>([]);
  const [totalSuccessCount, setTotalSuccessCount] = useState(0);
  const [totalFailCount, setTotalFailCount] = useState(0);
  const [totalResponseTime, setTotalResponseTime] = useState(0);
  const [totalBookingCount, setTotalBookingCount] = useState(0);

  // Refs for continuous load interval
  const continuousLoadRef = useRef<NodeJS.Timeout | null>(null);

  const addLog = useActivityLog((s) => s.addEntry);

  useEffect(() => {
    async function loadTrains() {
      try {
        const trainList = await api.listTrains();
        setTrains(trainList);
        if (trainList.length > 0) {
          setSelectedTrain(trainList[0].train_id);
        }
      } catch (err) {
        console.error("Failed to load trains", err);
      }
    }
    loadTrains();

    // Cleanup interval on unmount
    return () => stopContinuousLoad();
  }, []);

  function getRandomPassenger(): string {
    return PASSENGER_NAMES[Math.floor(Math.random() * PASSENGER_NAMES.length)];
  }

  // Helper to process a single booking without touching loading states (for loops)
  async function executeSingleBooking(passenger: string) {
    if (!selectedTrain) return;
    const startTime = performance.now();

    try {
      const result = await api.bookTicket(selectedTrain, passenger, selectedClass);
      const responseTime = performance.now() - startTime;

      const booking: BookingResult = {
        id: `${Date.now()}-${Math.random()}`,
        timestamp: Date.now(),
        success: true,
        booking_id: result.booking_id,
        train_name: result.train_name,
        passenger_name: passenger,
        response_time_ms: Math.round(responseTime),
        node_id: result.node_id,
      };

      setBookingHistory((prev) => [booking, ...prev].slice(0, 100));
      setTotalBookingCount((c) => c + 1);
      setTotalSuccessCount((c) => c + 1);
      setTotalResponseTime((t) => t + Math.round(responseTime));

      return true;
    } catch (err) {
      const responseTime = performance.now() - startTime;
      const errorMsg = err instanceof Error ? err.message : "Unknown error";

      const booking: BookingResult = {
        id: `${Date.now()}-${Math.random()}`,
        timestamp: Date.now(),
        success: false,
        passenger_name: passenger,
        response_time_ms: Math.round(responseTime),
        error: errorMsg,
      };

      setBookingHistory((prev) => [booking, ...prev].slice(0, 100));
      setTotalBookingCount((c) => c + 1);
      setTotalFailCount((c) => c + 1);
      setTotalResponseTime((t) => t + Math.round(responseTime));

      return false;
    }
  }

  async function handleBookTicket() {
    setIsBooking(true);
    const passenger = getRandomPassenger();
    const success = await executeSingleBooking(passenger);
    
    if (success) {
      addLog(`✓ Booking confirmed for ${passenger}`, "success");
    } else {
      addLog(`✗ Booking failed for ${passenger}`, "error");
    }
    setIsBooking(false);
  }

  async function handleBulkBooking() {
    setIsBulkBooking(true);
    addLog("Starting 20-user booking simulation...", "info");

    for (let i = 0; i < 20; i++) {
      const passenger = getRandomPassenger();
      await executeSingleBooking(passenger);
      await new Promise((resolve) => setTimeout(resolve, 200));
    }

    addLog("Bulk booking simulation complete", "success");
    setIsBulkBooking(false);
  }

  function startContinuousLoad() {
    if (continuousLoadRef.current) return;
    
    setIsContinuousLoad(true);
    addLog("Continuous traffic generation started (~3 req/sec)", "info");
    toast.success("Continuous load started");

    // Fire roughly 3 requests per second
    continuousLoadRef.current = setInterval(async () => {
      const passenger = getRandomPassenger();
      executeSingleBooking(passenger);
    }, 300); // 333ms = ~3 req/sec
  }

  function stopContinuousLoad() {
    if (continuousLoadRef.current) {
      clearInterval(continuousLoadRef.current);
      continuousLoadRef.current = null;
    }
    if (isContinuousLoad) {
      setIsContinuousLoad(false);
      addLog("Continuous traffic stopped", "info");
      toast.info("Continuous load stopped");
    }
  }

  const successRate = totalBookingCount > 0 ? (totalSuccessCount / totalBookingCount) * 100 : 0;
  const avgResponseTime = totalBookingCount > 0 ? Math.round(totalResponseTime / totalBookingCount) : 0;
  const selectedTrainInfo = trains.find((t) => t.train_id === selectedTrain);

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1fr_450px]">
        {/* Booking Form & Stats Column */}
        <div className="space-y-6">
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Train className="h-6 w-6 text-primary" />
                <h2 className="text-xl font-bold">IRCTC Booking Simulator</h2>
              </div>
              
              {/* Continuous Load Status Indicator */}
              {isContinuousLoad && (
                <div className="flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded-full animate-pulse">
                  <Activity className="h-4 w-4" />
                  <span className="text-sm font-semibold">Live Traffic Active</span>
                </div>
              )}
            </div>

            <div className="space-y-5">
              <div>
                <label className="mb-2 block text-sm font-medium text-muted-foreground">
                  Select Train Route
                </label>
                <select
                  value={selectedTrain}
                  onChange={(e) => setSelectedTrain(e.target.value)}
                  className="w-full rounded-md border border-border bg-background px-4 py-3 text-sm focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                >
                  {trains.map((train) => (
                    <option key={train.train_id} value={train.train_id}>
                      {train.name} — {train.source} → {train.destination} ({train.departure})
                    </option>
                  ))}
                </select>
              </div>

              {selectedTrainInfo && (
                <div className="flex items-center justify-between rounded-md border border-border bg-background/50 p-4 text-sm">
                  <div className="flex flex-col">
                    <span className="text-muted-foreground text-xs uppercase tracking-wider">Seats</span>
                    <span className="font-semibold text-lg">{selectedTrainInfo.available_seats}/{selectedTrainInfo.total_seats}</span>
                  </div>
                  <div className="h-8 w-px bg-border" />
                  <div className="flex flex-col">
                    <span className="text-muted-foreground text-xs uppercase tracking-wider">Price</span>
                    <span className="font-semibold text-lg">₹{selectedTrainInfo.price}</span>
                  </div>
                  <div className="h-8 w-px bg-border" />
                  <div className="flex flex-col">
                    <span className="text-muted-foreground text-xs uppercase tracking-wider">Departure</span>
                    <span className="font-semibold text-lg">{selectedTrainInfo.departure}</span>
                  </div>
                </div>
              )}

              <div>
                <label className="mb-2 block text-sm font-medium text-muted-foreground">
                  Class Preference
                </label>
                <div className="flex gap-2">
                  {SEAT_CLASSES.map((cls) => (
                    <button
                      key={cls}
                      onClick={() => setSelectedClass(cls)}
                      className={`rounded-md border px-5 py-2.5 text-sm font-medium transition-all ${
                        selectedClass === cls
                          ? "border-primary bg-primary text-primary-foreground shadow-md shadow-primary/20"
                          : "border-border bg-background hover:bg-secondary hover:border-muted-foreground/50"
                      }`}
                    >
                      {cls}
                    </button>
                  ))}
                </div>
              </div>

              {/* Action Buttons Grid */}
              <div className="grid grid-cols-2 gap-3 pt-4">
                <button
                  onClick={handleBookTicket}
                  disabled={isBooking || isContinuousLoad}
                  className="flex items-center justify-center gap-2 rounded-md bg-secondary border border-border px-4 py-3 text-sm font-semibold transition-colors hover:bg-secondary/80 disabled:opacity-50"
                >
                  <Ticket className="h-4 w-4" />
                  {isBooking ? "Booking..." : "Single Booking"}
                </button>

                <button
                  onClick={handleBulkBooking}
                  disabled={isBulkBooking || isContinuousLoad}
                  className="flex items-center justify-center gap-2 rounded-md border border-border bg-background px-4 py-3 text-sm font-medium transition-colors hover:bg-secondary disabled:opacity-50"
                >
                  {isBulkBooking ? "Simulating..." : "Burst 20 Users"}
                </button>
              </div>

              {/* Continuous Load Toggle */}
              <div className="pt-2">
                 {!isContinuousLoad ? (
                   <button
                     onClick={startContinuousLoad}
                     disabled={isBulkBooking}
                     className="w-full flex items-center justify-center gap-2 rounded-md bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-4 text-sm font-bold transition-all shadow-lg shadow-primary/25 disabled:opacity-50"
                   >
                     <Play className="h-5 w-5 fill-current" />
                     START CONTINUOUS LOAD
                   </button>
                 ) : (
                   <button
                     onClick={stopContinuousLoad}
                     className="w-full flex items-center justify-center gap-2 rounded-md bg-red-600 hover:bg-red-700 text-white px-4 py-4 text-sm font-bold transition-all shadow-lg shadow-red-500/25"
                   >
                     <Square className="h-5 w-5 fill-current" />
                     STOP LOAD
                   </button>
                 )}
              </div>
            </div>
          </div>

          {/* Real-time Stats Grid */}
          <div className="grid grid-cols-4 gap-4">
            <div className="rounded-lg border border-border bg-card p-4 text-center shadow-sm">
              <div className="text-3xl font-black tracking-tight">{totalBookingCount}</div>
              <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground mt-1">Total</div>
            </div>
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4 text-center shadow-sm">
              <div className="text-3xl font-black tracking-tight text-emerald-500">{totalSuccessCount}</div>
              <div className="text-xs font-medium uppercase tracking-wider text-emerald-500/70 mt-1">Success</div>
            </div>
            <div className={`rounded-lg border p-4 text-center shadow-sm transition-colors duration-300 ${totalFailCount > 0 ? "border-red-500/50 bg-red-500/15" : "border-border bg-card"}`}>
              <div className={`text-3xl font-black tracking-tight ${totalFailCount > 0 ? "text-red-500" : "text-muted-foreground"}`}>{totalFailCount}</div>
              <div className={`text-xs font-medium uppercase tracking-wider mt-1 ${totalFailCount > 0 ? "text-red-500/70" : "text-muted-foreground"}`}>Failed</div>
            </div>
            <div className={`rounded-lg border p-4 text-center shadow-sm transition-colors duration-300 ${
              avgResponseTime > 1000 ? "border-red-500/50 bg-red-500/15" : 
              avgResponseTime > 400 ? "border-amber-500/50 bg-amber-500/10" : 
              "border-border bg-card"
            }`}>
              <div className={`text-3xl font-black tracking-tight ${
                avgResponseTime > 1000 ? "text-red-500" : 
                avgResponseTime > 400 ? "text-amber-500" : 
                "text-foreground"
              }`}>
                {avgResponseTime}<span className="text-lg font-medium opacity-50">ms</span>
              </div>
              <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground mt-1">Avg Time</div>
            </div>
          </div>
        </div>

        {/* Live Booking History Column */}
        <div className="flex flex-col h-[700px] rounded-lg border border-border bg-card shadow-sm">
          <div className="flex items-center justify-between border-b border-border p-5">
            <h3 className="font-semibold text-lg">Live Booking Feed</h3>
            <div className={`px-3 py-1 rounded-full text-xs font-bold ${
              successRate >= 95 ? "bg-emerald-500/20 text-emerald-400" : 
              successRate >= 80 ? "bg-yellow-500/20 text-yellow-400" : 
              "bg-red-500/20 text-red-400"
            }`}>
              {successRate.toFixed(1)}% SUCCESS
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {bookingHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground opacity-60">
                <Ticket className="h-12 w-12 mb-3" />
                <p>Awaiting bookings...</p>
              </div>
            ) : (
              bookingHistory.map((booking) => (
                <div
                  key={booking.id}
                  className={`rounded-md border p-3.5 text-sm transition-all animate-in slide-in-from-left-4 fade-in duration-300 ${
                    !booking.success
                      ? "border-red-500/40 bg-red-500/10"
                      : booking.response_time_ms > 2000
                        ? "border-red-500/40 bg-red-500/10"
                        : booking.response_time_ms > 1000
                          ? "border-amber-500/40 bg-amber-500/10"
                          : booking.response_time_ms > 400
                            ? "border-yellow-500/40 bg-yellow-500/10"
                            : "border-emerald-500/30 bg-emerald-500/5"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      {!booking.success ? (
                        <XCircle className="h-4 w-4 text-red-500" />
                      ) : booking.response_time_ms > 2000 ? (
                        <XCircle className="h-4 w-4 text-red-500" />
                      ) : booking.response_time_ms > 1000 ? (
                        <Clock className="h-4 w-4 text-amber-500" />
                      ) : booking.response_time_ms > 400 ? (
                        <Clock className="h-4 w-4 text-yellow-500" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      )}
                      <span className={`font-bold tracking-tight ${!booking.success ? "text-red-500" : ""}`}>
                        {!booking.success
                          ? "FAILED"
                          : booking.response_time_ms > 2000
                            ? "CRITICAL LAG"
                            : booking.booking_id}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs">
                      <Clock className="h-3 w-3 opacity-60" />
                      <span
                        className={`font-mono text-[13px] ${
                          booking.response_time_ms > 2000 ? "font-black text-red-400"
                          : booking.response_time_ms > 1000 ? "font-bold text-amber-400"
                          : booking.response_time_ms > 400 ? "font-bold text-yellow-400"
                          : "text-muted-foreground"
                        }`}
                      >
                        {booking.response_time_ms}ms
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2.5 text-xs text-muted-foreground/80 mt-1">
                    <span className="font-medium text-foreground/80">{booking.passenger_name}</span>
                    {booking.train_name && (
                      <>
                        <span className="opacity-40">•</span>
                        <span className="truncate max-w-[120px]">{booking.train_name}</span>
                      </>
                    )}
                    {booking.node_id && (
                      <>
                        <span className="opacity-40">•</span>
                        <div className="flex items-center gap-1 px-1.5 py-0.5 bg-background/50 rounded border border-border/50">
                          <Server className="h-3 w-3" />
                          <span className="font-mono">{booking.node_id}</span>
                        </div>
                      </>
                    )}
                  </div>

                  {booking.error && (
                    <div className="mt-2 text-xs font-medium text-red-400 bg-red-950/30 p-2 rounded">
                      {booking.error}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}