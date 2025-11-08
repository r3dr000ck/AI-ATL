// Generate realistic dummy data for the trading dashboard

export interface Position {
  symbol: string;
  name: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  chartData: { time: string; price: number }[];
}

export interface PortfolioDataPoint {
  date: string;
  value: number;
}

export interface AccountSummary {
  totalValue: number;
  buyingPower: number;
  realizedPnL: number;
  unrealizedPnL: number;
  totalPnL: number;
  totalPnLPercent: number;
  cashBalance: number;
}

// Generate random walk price data for a stock
function generatePriceChart(
  basePrice: number,
  points: number,
  volatility: number = 0.02,
  trend: number = 0
): { time: string; price: number }[] {
  const data: { time: string; price: number }[] = [];
  let price = basePrice;
  const now = new Date();

  for (let i = points; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 5 * 60 * 1000); // 5-minute intervals
    const change = (Math.random() - 0.5) * volatility * price + trend * price;
    price = Math.max(price + change, basePrice * 0.5); // Don't let it drop below 50%

    data.push({
      time: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      price: parseFloat(price.toFixed(2))
    });
  }

  return data;
}

// Generate portfolio value over time
export function generatePortfolioHistory(
  days: number,
  startValue: number,
  endValue: number
): PortfolioDataPoint[] {
  const data: PortfolioDataPoint[] = [];
  const totalChange = endValue - startValue;
  const now = new Date();

  for (let i = days; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
    const progress = 1 - (i / days);

    // Add some randomness while trending toward end value
    const baseValue = startValue + (totalChange * progress);
    const randomVariation = (Math.random() - 0.5) * (startValue * 0.03);
    const value = baseValue + randomVariation;

    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      value: parseFloat(value.toFixed(2))
    });
  }

  return data;
}

// Generate current positions
export function generatePositions(): Position[] {
  const stocks = [
    { symbol: 'NQ', name: 'Nasdaq-100 E-Mini Futures', basePrice: 20150, trend: 0.0002 },
    { symbol: 'ES', name: 'S&P 500 E-Mini Futures', basePrice: 5875, trend: 0.0001 },
    { symbol: 'CL', name: 'Crude Oil Futures', basePrice: 71.5, trend: -0.0001 },
    { symbol: 'GC', name: 'Gold Futures', basePrice: 2665, trend: 0.0003 },
    { symbol: 'ZB', name: '30-Year T-Bond Futures', basePrice: 118.5, trend: 0.0001 },
  ];

  return stocks.map(stock => {
    const avgPrice = stock.basePrice * (0.95 + Math.random() * 0.1);
    const chartData = generatePriceChart(stock.basePrice, 72, 0.008, stock.trend);
    const currentPrice = chartData[chartData.length - 1].price;
    const quantity = Math.floor(Math.random() * 10) + 2;
    const marketValue = currentPrice * quantity;
    const costBasis = avgPrice * quantity;
    const unrealizedPnL = marketValue - costBasis;
    const unrealizedPnLPercent = (unrealizedPnL / costBasis) * 100;

    return {
      symbol: stock.symbol,
      name: stock.name,
      quantity,
      avgPrice: parseFloat(avgPrice.toFixed(2)),
      currentPrice,
      marketValue: parseFloat(marketValue.toFixed(2)),
      unrealizedPnL: parseFloat(unrealizedPnL.toFixed(2)),
      unrealizedPnLPercent: parseFloat(unrealizedPnLPercent.toFixed(2)),
      chartData
    };
  });
}

// Generate account summary
export function generateAccountSummary(positions: Position[]): AccountSummary {
  const totalMarketValue = positions.reduce((sum, pos) => sum + pos.marketValue, 0);
  const totalUnrealizedPnL = positions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0);
  const realizedPnL = 12350.75; // Dummy realized P&L
  const totalPnL = realizedPnL + totalUnrealizedPnL;
  const cashBalance = 45000;
  const totalValue = totalMarketValue + cashBalance;
  const buyingPower = cashBalance * 4; // 4x leverage for futures
  const totalPnLPercent = (totalPnL / (totalValue - totalPnL)) * 100;

  return {
    totalValue: parseFloat(totalValue.toFixed(2)),
    buyingPower: parseFloat(buyingPower.toFixed(2)),
    realizedPnL: parseFloat(realizedPnL.toFixed(2)),
    unrealizedPnL: parseFloat(totalUnrealizedPnL.toFixed(2)),
    totalPnL: parseFloat(totalPnL.toFixed(2)),
    totalPnLPercent: parseFloat(totalPnLPercent.toFixed(2)),
    cashBalance: parseFloat(cashBalance.toFixed(2))
  };
}
