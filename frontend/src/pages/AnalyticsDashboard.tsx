// frontend/src/pages/AnalyticsDashboard.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer 
} from 'recharts';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { 
  TrendingUp, Users, Clock, DollarSign 
} from "lucide-react";
import { fetchAnalyticsData, fetchPredictiveInsights } from '../api/analytics';

// Define types for analytics data
interface MeetingTrend {
  date: string;
  meetings: number;
  duration: number;
}

interface TeamProductivity {
  team: string;
  productivityScore: number;
  meetingsAttended: number;
  avgMeetingDuration: number;
}

interface PredictiveInsight {
  month: string;
  predictedMeetings: number;
  confidence: number;
}

interface ROIData {
  investment: number;
  savings: number;
  roi: number;
}

const AnalyticsDashboard: React.FC = () => {
  // State management for ROI calculator
  const [investment, setInvestment] = useState<number>(10000);
  const [savings, setSavings] = useState<number>(15000);
  const [calculatedROI, setCalculatedROI] = useState<ROIData | null>(null);

  // Fetch analytics data using React Query
  const { 
    data: analyticsData, 
    isLoading, 
    error 
  } = useQuery({
    queryKey: ['analytics'],
    queryFn: fetchAnalyticsData,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 2, // Retry failed requests twice
  });

  // Fetch predictive insights
  const { 
    data: predictiveData, 
    isLoading: isPredictiveLoading, 
    error: predictiveError 
  } = useQuery({
    queryKey: ['predictiveInsights'],
    queryFn: fetchPredictiveInsights,
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes
    retry: 2,
  });

  // Calculate ROI when inputs change
  useEffect(() => {
    if (investment > 0 && savings >= 0) {
      const roi = ((savings - investment) / investment) * 100;
      setCalculatedROI({
        investment,
        savings,
        roi: Number(roi.toFixed(2))
      });
    }
  }, [investment, savings]);

  // Memoize chart data to prevent unnecessary re-renders
  const meetingTrendsData = useMemo(() => analyticsData?.meetingTrends || [], [analyticsData]);
  const productivityData = useMemo(() => analyticsData?.teamProductivity || [], [analyticsData]);
  const predictiveInsights = useMemo(() => predictiveData || [], [predictiveData]);

  // Handle loading state
  if (isLoading || isPredictiveLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full"
        />
      </div>
    );
  }

  // Handle error state with user-friendly message
  if (error || predictiveError) {
    return (
      <div className="flex flex-col items-center justify-center h-screen p-4">
        <Card className="bg-destructive/10 border-destructive/20">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Data</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              We encountered an issue loading the analytics data. Please try again later.
            </p>
            <Button 
              className="mt-4" 
              onClick={() => window.location.reload()}
            >
              Refresh Page
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center"
      >
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
      </motion.div>

      {/* Meeting Trends Section */}
      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-xl">Meeting Trends</CardTitle>
          <TrendingUp className="w-5 h-5 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={meetingTrendsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="date" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="meetings" stroke="#3b82f6" name="Meetings" />
                <Line type="monotone" dataKey="duration" stroke="#10b981" name="Total Duration (hrs)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Team Productivity Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-xl">Team Productivity</CardTitle>
            <Users className="w-5 h-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={productivityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="team" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="productivityScore" fill="#3b82f6" name="Productivity Score" />
                  <Bar dataKey="meetingsAttended" fill="#10b981" name="Meetings Attended" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Predictive Insights Section */}
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-xl">Predictive Insights</CardTitle>
            <Clock className="w-5 h-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={predictiveInsights}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ month, predictedMeetings }) => `${month}: ${predictedMeetings}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="predictedMeetings"
                  >
                    {predictiveInsights.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={['#3b82f6', '#10b981', '#f59e0b'][index % 3]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ROI Calculator Section */}
      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-xl">ROI Calculator</CardTitle>
          <DollarSign className="w-5 h-5 text-muted-foreground" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="investment" className="block text-sm font-medium mb-1">
                Investment ($)
              </label>
              <Input
                id="investment"
                type="number"
                value={investment}
                onChange={(e) => setInvestment(Math.max(0, parseFloat(e.target.value) || 0))}
                className="w-full"
                min="0"
                step="100"
                aria-label="Investment amount in dollars"
              />
            </div>
            <div>
              <label htmlFor="savings" className="block text-sm font-medium mb-1">
                Savings ($)
              </label>
              <Input
                id="savings"
                type="number"
                value={savings}
                onChange={(e) => setSavings(Math.max(0, parseFloat(e.target.value) || 0))}
                className="w-full"
                min="0"
                step="100"
                aria-label="Savings amount in dollars"
              />
            </div>
          </div>
          {calculatedROI && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 p-4 bg-muted rounded-lg"
            >
              <p className="text-lg font-semibold">
                ROI: {calculatedROI.roi}%
              </p>
              <p className="text-sm text-muted-foreground">
                Investment: ${calculatedROI.investment.toLocaleString()} | Savings: ${calculatedROI.savings.toLocaleString()}
              </p>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsDashboard;