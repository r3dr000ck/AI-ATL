const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Position {
  ticker: string;
  quantity: number;
  entry_price: number;
  current_price?: number;
  pnl?: number;
  pnl_pct?: number;
}

export interface TradeRequest {
  ticker: string;
  action: 'BUY' | 'SELL';
  s_final?: number;
  quantity?: number;
  reason?: string;
}

export interface TradeResponse {
  success: boolean;
  order_id?: string;
  ticker: string;
  action: string;
  quantity: number;
  price?: number;
  message: string;
  timestamp: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  broker_capital: number;
  num_positions: number;
  num_events: number;
}

export interface CapitalInfo {
  available_capital: number;
  total_exposure: number;
}

export interface PositionsResponse {
  positions: Position[];
  total_exposure: number;
  capital: number;
}

export interface PriceMovement {
  ticker: string;
  name?: string;
  previous_close: number;
  current_price: number;
  change: number;
  change_pct: number;
  volume: number;
}

export interface DailyMovementsResponse {
  jumps: PriceMovement[];
  dips: PriceMovement[];
  timestamp: string;
}

export interface BigMoversResponse {
  movers: PriceMovement[];
  timestamp: string;
}

export interface NewsItem {
  id: number;
  headline: string;
  summary: string;
  source: string;
  url: string;
  image: string;
  datetime: number;
  datetime_formatted?: string;
  category: string;
  related: string;
}

export interface MarketNewsResponse {
  news: NewsItem[];
  timestamp: string;
  source: string;
}

export interface EquityCurvePoint {
  time: number;
  equity: number;
  change_pct: number;
  timestamp: number;
  normalized: number;
}

export interface EquityCurveResponse {
  equity_curve: EquityCurvePoint[];
  current_equity: number;
  starting_equity: number;
  total_pnl: number;
  timestamp: string;
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: response.statusText }));
        throw new Error(error.message || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/health');
  }

  async executeTrade(trade: TradeRequest): Promise<TradeResponse> {
    return this.request<TradeResponse>('/execution/trade', {
      method: 'POST',
      body: JSON.stringify(trade),
    });
  }

  async getPositions(): Promise<PositionsResponse> {
    return this.request<PositionsResponse>('/execution/positions');
  }

  async getCapital(): Promise<CapitalInfo> {
    return this.request<CapitalInfo>('/execution/capital');
  }

  async getDailyMovements(): Promise<DailyMovementsResponse> {
    return this.request<DailyMovementsResponse>('/market/daily-movements');
  }

  async getBigMovers(): Promise<BigMoversResponse> {
    return this.request<BigMoversResponse>('/market/big-movers');
  }

  async getMarketNews(limit: number = 20, category: string = 'general'): Promise<MarketNewsResponse> {
    return this.request<MarketNewsResponse>(`/market/news?limit=${limit}&category=${category}`);
  }

  async getEquityCurve(): Promise<EquityCurveResponse> {
    return this.request<EquityCurveResponse>('/market/equity-curve');
  }
}

export const apiClient = new APIClient();
