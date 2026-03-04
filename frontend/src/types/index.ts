export interface Transaction {
    tx_id: string;
    timestamp: number;
    amount: number;
    illicit_probability: number; // 0.0 to 1.0
    threshold: number;
    flagged: boolean;
    inference_latency_ms: number;
}
