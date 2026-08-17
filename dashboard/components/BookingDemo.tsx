"use client";

import { useEffect, useState } from "react";
import {
  Train,
  CheckCircle2,
  XCircle,
  Clock,
  Server,
  Ticket,
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
];

const SEAT_CLASSES = ["SL", "3A", "2A", "1A"];

export function BookingDemo() {
  const [trains, setTrains] = useState<TrainInfo[]>([]);
  const [selectedTrain, setSelectedTrain] = useState<string>("");
  const [selectedClass, setSelectedClass] = useState<string>("3A");
  const [isBooking, setIsBooking] = useState(false);
  const [isBulkBooking, setIsBulkBooking] = useState(false);
  const [bookingHistory, setBookingHistory] = useState<BookingResult[]>([]);

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
  }, []);

  function getRandomPassenger(): string {
    return PASSENGER_NAMES[Math.floor(Math.random() * PASSENGER_NAMES.length)];
  }

  async function handleBookTicket() {
    if (!selectedTrain) return;
    setIsBooking(true);

    const passenger = getRandomPassenger();
    const startTime = performance.now();

    try {
      const result = await api.bookTicket(
        selectedTrain,
        passenger,
        selectedClass,
      );

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

      setBookingHistory((prev) => [booking, ...prev].slice(0, 50));
      addLog(
        `✓ Booking ${result.booking_id} confirmed on ${result.node_id} (${Math.round(responseTime)}ms)`,
        "success",
      );
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

      setBookingHistory((prev) => [booking, ...prev].slice(0, 50));
      addLog(`✗ Booking failed: ${errorMsg} (${Math.round(responseTime)}ms)`, "error");
    } finally {
      setIsBooking(false);
    }
  }

  async function handleBulkBooking() {
    setIsBulkBooking(true);
    addLog("Starting bulk booking simulation (20 requests)...", "info");

    for (let i = 0; i < 20; i++) {
      await handleBookTicket();
      await new Promise((resolve) => setTimeout(resolve, 200));
    }

    addLog("Bulk booking simulation complete", "success");
    setIsBulkBooking(false);
  }

  const successCount = bookingHistory.filter((b) => b.success).length;
  const failCount = bookingHistory.filter((b) => !b.success).length;
  const totalCount = bookingHistory.length;
  const successRate = totalCount > 0 ? (successCount / totalCount) * 100 : 0;
  const avgResponseTime =
    totalCount > 0
      ? Math.round(
          bookingHistory.reduce((sum, b) => sum + b.response_time_ms, 0) /
            totalCount,
        )
      : 0;

  const selectedTrainInfo = trains.find((t) => t.train_id === selectedTrain);

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
        {/* Booking Form */}
        <div className="space-y-6">
          <div className="rounded-lg border border-border bg-card p-6">
            <div className="mb-6 flex items-center gap-3">
              <Train className="h-6 w-6 text-primary" />
              <h2 className="text-xl font-bold">IRCTC Booking Simulator</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-muted-foreground">
                  Select Train
                </label>
                <select
                  value={selectedTrain}
                  onChange={(e) => setSelectedTrain(e.target.value)}
                  className="w-full rounded-md border border-border bg-background px-4 py-3 text-sm"
                >
                  {trains.map((train) => (
                    <option key={train.train_id} value={train.train_id}>
                      {train.name} — {train.source} → {train.destination} ({train.departure})
                    </option>
                  ))}
                </select>
              </div>

              {selectedTrainInfo && (
                <div className="flex items-center gap-4 rounded-md border border-border bg-background/50 p-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Seats: </span>
                    <span className="font-semibold">
                      {selectedTrainInfo.available_seats}/{selectedTrainInfo.total_seats}
                    </span>
                  </div>
                  <div className="h-4 w-px bg-border" />
                  <div>
                    <span className="text-muted-foreground">Price: </span>
                    <span className="font-semibold">₹{selectedTrainInfo.price}</span>
                  </div>
                  <div className="h-4 w-px bg-border" />
                  <div>
                    <span className="text-muted-foreground">Departure: </span>
                    <span className="font-semibold">{selectedTrainInfo.departure}</span>
                  </div>
                </div>
              )}

              <div>
                <label className="mb-2 block text-sm font-medium text-muted-foreground">
                  Class
                </label>
                <div className="flex gap-2">
                  {SEAT_CLASSES.map((cls) => (
                    <button
                      key={cls}
                      onClick={() => setSelectedClass(cls)}
                      className={`rounded-md border px-4 py-2 text-sm font-medium transition-colors ${
                        selectedClass === cls
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border bg-background hover:bg-secondary"
                      }`}
                    >
                      {cls}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleBookTicket}
                  disabled={isBooking || isBulkBooking}
                  className="flex flex-1 items-center justify-center gap-2 rounded-md bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                >
                  <Ticket className="h-4 w-4" />
                  {isBooking ? "Booking..." : "Book Now"}
                </button>

                <button
                  onClick={handleBulkBooking}
                  disabled={isBooking || isBulkBooking}
                  className="flex items-center gap-2 rounded-md border border-border bg-background px-6 py-3 text-sm font-medium transition-colors hover:bg-secondary disabled:opacity-50"
                >
                  {isBulkBooking ? "Simulating..." : "Simulate 20 Users"}
                </button>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="rounded-lg border border-border bg-card p-4 text-center">
              <div className="text-2xl font-bold">{totalCount}</div>
              <div className="text-xs text-muted-foreground">Total</div>
            </div>
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4 text-center">
              <div className="text-2xl font-bold text-emerald-500">{successCount}</div>
              <div className="text-xs text-muted-foreground">Success</div>
            </div>
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-center">
              <div className="text-2xl font-bold text-red-500">{failCount}</div>
              <div className="text-xs text-muted-foreground">Failed</div>
            </div>
            <div className="rounded-lg border border-border bg-card p-4 text-center">
              <div className="text-2xl font-bold">{avgResponseTime}ms</div>
              <div className="text-xs text-muted-foreground">Avg Time</div>
            </div>
          </div>
        </div>

        {/* Booking History */}
        <div className="rounded-lg border border-border bg-card">
          <div className="border-b border-border p-4">
            <h3 className="font-semibold">Booking History</h3>
            <p className="text-xs text-muted-foreground">
              Success rate: {successRate.toFixed(1)}%
            </p>
          </div>

          <div className="h-[500px] overflow-y-auto p-4">
            {bookingHistory.length === 0 ? (
              <p className="pt-8 text-center text-sm text-muted-foreground">
                Click "Book Now" to start
              </p>
            ) : (
              <div className="space-y-2">
                {bookingHistory.map((booking) => (
                  <div
                    key={booking.id}
                    className={`rounded-md border p-3 text-sm ${
                      booking.success
                        ? "border-emerald-500/30 bg-emerald-500/5"
                        : "border-red-500/30 bg-red-500/5"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {booking.success ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <span className="font-medium">
                          {booking.success ? booking.booking_id : "FAILED"}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {booking.response_time_ms}ms
                      </div>
                    </div>

                    <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{booking.passenger_name}</span>
                      {booking.train_name && (
                        <>
                          <span>·</span>
                          <span>{booking.train_name}</span>
                        </>
                      )}
                      {booking.node_id && (
                        <>
                          <span>·</span>
                          <div className="flex items-center gap-1">
                            <Server className="h-3 w-3" />
                            {booking.node_id}
                          </div>
                        </>
                      )}
                    </div>

                    {booking.error && (
                      <div className="mt-1 text-xs text-red-400">
                        {booking.error}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}