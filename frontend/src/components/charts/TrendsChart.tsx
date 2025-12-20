// frontend/src/components/charts/TrendsChart.tsx
import React, { useEffect, useRef, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import { toast } from 'react-toastify';
import { format } from 'date-fns';

// Types for chart data and API response
interface TrendDataPoint {
  date: string;
  meetings: number;
  productivity: number;
  predictedMeetings?: number;
  roiImpact: number;
}

interface TrendsChartProps {
  startDate: Date;
  endDate: Date;
  teamId: string;
}

// Utility to format data for the chart
const formatDate = (date: string): string => {
  try {
    return format(new Date(date), 'MMM dd');
  } catch (error) {
    console.error('Date formatting error:', error);
    return 'Invalid Date';
  }
};

const TrendsChart: React.FC<TrendsChartProps> = ({ startDate, endDate, teamId }) => {
  const [chartData, setChartData] = useState<TrendDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const chartContainerRef = useRef<HTMLDivElement>(null);

  // Fetch trends data from API
  useEffect(() => {
    const fetchTrendsData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Construct API URL with query parameters for date range and team
        const apiUrl = new URL('/api/analytics/trends', window.location.origin);
        apiUrl.searchParams.append('startDate', startDate.toISOString());
        apiUrl.searchParams.append('endDate', endDate.toISOString());
        apiUrl.searchParams.append('teamId', teamId);

        const response = await fetch(apiUrl.toString(), {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            // Include authorization token if available (security best practice)
            'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`,
          },
        });

        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }

        const data: TrendDataPoint[] = await response.json();
        // Format dates for display and ensure data integrity
        const formattedData = data.map((point) => ({
          ...point,
          date: formatDate(point.date),
        }));
        setChartData(formattedData);
      } catch (err) {
        console.error('Error fetching trends data:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to load trends data';
        setError(errorMessage);
        toast.error(errorMessage, { position: 'top-right' });
      } finally {
        setIsLoading(false);
      }
    };

    fetchTrendsData();
  }, [startDate, endDate, teamId]);

  // Custom tooltip for better UX
  const CustomTooltip: React.FC<{ active: boolean; payload: any[] }> = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 rounded-lg shadow-md border border-gray-200">
          <p className="font-semibold text-gray-800">{`Date: ${payload[0].payload.date}`}</p>
          <p className="text-blue-600">{`Meetings: ${payload[0].value}`}</p>
          <p className="text-green-600">{`Productivity: ${payload[1].value}%`}</p>
          {payload[2]?.value && (
            <p className="text-purple-600">{`Predicted Meetings: ${payload[2].value}`}</p>
          )}
          <p className="text-red-600">{`ROI Impact: $${payload[3].value.toFixed(2)}`}</p>
        </div>
      );
    }
    return null;
  };

  // Render loading state
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-96">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="flex justify-center items-center h-96 text-red-600">
        <p>{error}</p>
      </div>
    );
  }

  // Render empty state if no data
  if (chartData.length === 0) {
    return (
      <div className="flex justify-center items-center h-96 text-gray-600">
        <p>No data available for the selected period.</p>
      </div>
    );
  }

  return (
    <motion.div
      ref={chartContainerRef}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-white p-6 rounded-lg shadow-md w-full h-96"
    >
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Meeting & Productivity Trends</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => value}
          />
          <YAxis
            yAxisId="left"
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
            label={{ value: 'Count', angle: -90, position: 'insideLeft', style: { textFill: '#6b7280' } }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#6b7280"
            tick={{ fontSize: 12 }}
            label={{ value: 'Productivity (%)', angle: 90, position: 'insideRight', style: { textFill: '#6b7280' } }}
          />
          <Tooltip content={<CustomTooltip active={false} payload={[]} />} />
          <Legend verticalAlign="bottom" height={36} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="meetings"
            stroke="#3b82f6"
            name="Meetings"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="productivity"
            stroke="#10b981"
            name="Productivity"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="predictedMeetings"
            stroke="#8b5cf6"
            name="Predicted Meetings (ML)"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="roiImpact"
            stroke="#ef4444"
            name="ROI Impact ($)"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  );
};

export default TrendsChart;