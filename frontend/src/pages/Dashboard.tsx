import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { crmApi, calendarApi, authApi, leadApi } from '@/lib/api';
import { LeadStatisticsOverview, LeadEngagementGroupResponse, LeadLocationGroupResponse, BulkMessageGroup, CalendarSummaryResponse } from '@/lib/api';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { PieChart as RechartsPieChart, Pie, Label, LineChart as RechartsLineChart, Line, XAxis, CartesianGrid, ResponsiveContainer, BarChart, YAxis, Tooltip, Bar, Cell } from "recharts";
import { Skeleton } from "@/components/ui/skeleton";

// Add IntegrationStatistics type inline
interface IntegrationStatistics {
  total_messages: number;
  total_conversations: number;
  average_messages_per_lead: number;
}

// Utility to get CSS variable as HSL string
function getCssVarHsl(varName: string, fallback: string) {
  if (typeof window === 'undefined') return fallback;
  const root = window.getComputedStyle(document.documentElement);
  const value = root.getPropertyValue(varName).trim();
  return value ? `hsl(${value})` : fallback;
}

export default function Dashboard() {
  const [leadStats, setLeadStats] = useState<LeadStatisticsOverview | null>(null);
  const [integrationStats, setIntegrationStats] = useState<IntegrationStatistics | null>(null);
  const [engagementStats, setEngagementStats] = useState<LeadEngagementGroupResponse | null>(null);
  const [locationStats, setLocationStats] = useState<LeadLocationGroupResponse | null>(null);
  const [bulkMessages, setBulkMessages] = useState<BulkMessageGroup[]>([]);
  const [calendarSummary, setCalendarSummary] = useState<CalendarSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const userId = await authApi.getUserId();

        // Fetch Lead Statistics Overview
        const leadStatsResponse = await leadApi.getLeadStatisticsOverview();
        setLeadStats(leadStatsResponse);

        // Fetch Integration Statistics
        const integrationStatsResponse = await crmApi.getIntegrationStatistics(userId);
        setIntegrationStats(integrationStatsResponse);

        // Fetch Lead Engagement Groups
        const engagementResponse = await leadApi.groupLeadsByEngagement();
        setEngagementStats(engagementResponse);

        // Fetch Lead Location Groups
        const locationResponse = await leadApi.groupLeadsByLocation();
        setLocationStats(locationResponse);

        // Fetch Recent Bulk Messages
        const bulkMessagesResponse = await crmApi.getBulkMessageGroups(userId);
        setBulkMessages(bulkMessagesResponse.slice(0, 5)); // Limit to 5 on client side

        // Fetch Calendar Summary (last 30 days)
        const today = new Date();
        const startDate = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        const endDate = today.toISOString().split('T')[0];
        const calendarResponse = await calendarApi().getCalendarSummary({});
        setCalendarSummary(calendarResponse);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred while fetching data');
        toast("Failed to load dashboard data", {
          description: "Please try again later or contact support if the issue persists."
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  // Get colors from CSS variables
  const destructiveColor = getCssVarHsl('--destructive', 'hsl(0, 65%, 55%)');
  const mutedColor = getCssVarHsl('--muted', 'hsl(220, 8%, 90%)');
  const primaryColor = getCssVarHsl('--primary', 'hsl(220, 25%, 8%)');

  // Prepare data for Engagement Pie Chart
  const engagementChartData = engagementStats ? [
    { category: "no_contact_info", leads: engagementStats.groups?.no_contact_info ?? 0, fill: destructiveColor },
    { category: "basic_contact_info", leads: engagementStats.groups?.basic_contact_info ?? 0, fill: mutedColor },
    { category: "multiple_contact_points", leads: engagementStats.groups?.multiple_contact_points ?? 0, fill: primaryColor }
  ] : [];

  const engagementChartConfig = {
    no_contact_info: { label: "No Contact Info", color: destructiveColor },
    basic_contact_info: { label: "Basic Contact Info", color: mutedColor },
    multiple_contact_points: { label: "Multiple Contact Points", color: primaryColor }
  };

  // Calculate total leads for pie chart
  const totalLeads = React.useMemo(() => {
    return engagementChartData.reduce((acc, curr) => acc + curr.leads, 0);
  }, [engagementChartData]);

  // Prepare data for Events by Day Line Chart
  const eventsChartData = calendarSummary ? Object.keys(calendarSummary.events_by_day).sort().map(date => ({
    date,
    events: calendarSummary.events_by_day[date].length
  })) : [];

  const eventsChartConfig = {
    events: { label: "Events per Day", color: "#4D96FF" }
  };

  // Calculate total events for line chart
  const totalEvents = React.useMemo(() => ({
    events: eventsChartData.reduce((acc, curr) => acc + curr.events, 0)
  }), [eventsChartData]);

  // Prepare top locations for table
  const topLocations = locationStats ? Object.entries(locationStats.groups).flatMap(([country, states]) =>
    Object.entries(states).flatMap(([state, cities]) =>
      Object.entries(cities).map(([city, count]) => ({
        country,
        state,
        city,
        count
      }))
    )).sort((a, b) => b.count - a.count).slice(0, 5) : [];

  if (isLoading) {
    return (
      <div className="p-8 min-h-screen">
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">CRM Dashboard</h1>
            <p className="text-muted-foreground">Overview of lead statistics, engagement, and outreach activities</p>
          </div>
          {/* Skeletons for Lead Statistics Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-32 mb-2" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-20 mb-2" />
                  <Skeleton className="h-4 w-40" />
                </CardContent>
              </Card>
            ))}
          </div>
          {/* Skeletons for Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {[...Array(2)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-40 mb-2" />
                  <Skeleton className="h-4 w-60" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-48 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
          {/* Skeleton for Top Locations Table */}
          <Card className="border ">
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    {[...Array(4)].map((_, i) => (
                      <TableHead key={i}><Skeleton className="h-4 w-20" /></TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[...Array(5)].map((_, i) => (
                    <TableRow key={i}>
                      {[...Array(4)].map((_, j) => (
                        <TableCell key={j}><Skeleton className="h-4 w-16" /></TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
          {/* Skeleton for Recent Bulk Messages Table */}
          <Card className="border ">
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    {[...Array(6)].map((_, i) => (
                      <TableHead key={i}><Skeleton className="h-4 w-20" /></TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[...Array(5)].map((_, i) => (
                    <TableRow key={i}>
                      {[...Array(6)].map((_, j) => (
                        <TableCell key={j}><Skeleton className="h-4 w-16" /></TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <p className="text-red-500">Error: {error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 bg-black text-white px-4 py-2 rounded hover:bg-gray-800"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-8 min-h-screen">
      <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">CRM Dashboard</h1>
        <p className="text-muted-foreground">Overview of lead statistics, engagement, and outreach activities</p>
        </div>
        {/* Lead Statistics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Total Leads</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{leadStats?.total_leads || 0}</p>
              <p className="text-sm text-muted-foreground">Total leads in the system</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Total Messages</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{integrationStats?.total_messages || 0}</p>
              <p className="text-sm text-muted-foreground">Messages sent across all platforms</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Avg. Messages per Lead</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{integrationStats?.average_messages_per_lead?.toFixed(2) || 0}</p>
              <p className="text-sm text-muted-foreground">Average messages sent per lead</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Lead Engagement Pie Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-black">Lead Engagement</CardTitle>
              <CardDescription>
                Distribution of leads by engagement level
              </CardDescription>
            </CardHeader>
            <CardContent>
              {engagementStats && (
                // <ChartContainer
                //   config={engagementChartConfig}
                //   className="w-full h-[250px]"
                // >
                  <ResponsiveContainer width="100%" height={250} >
                    <RechartsPieChart>
                      <Pie
                        data={engagementChartData}
                        dataKey="leads"
                        nameKey="category"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label={({ category, percent }) => `${engagementChartConfig[category].label}: ${(percent * 100).toFixed(0)}%`}
                      >
                        {engagementChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value, name, props) => [`${value} leads`, engagementChartConfig[props.payload.category].label]}
                      />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                // </ChartContainer>
              )}
              {(!engagementStats || totalLeads === 0) && (
                <p className="text-gray-500 text-center py-8">No engagement data available</p>
              )}
              <div className="flex flex-wrap gap-4 mt-4">
                {engagementChartData.map((entry) => (
                  <div key={entry.category} className="flex items-center gap-2">
                    <span style={{ background: entry.fill, width: 16, height: 16, display: 'inline-block', borderRadius: 4 }} />
                    <span className="text-sm text-black">{engagementChartConfig[entry.category].label}</span>
                  </div>
                ))}
              </div>
              
            </CardContent>
          </Card>

          {/* Events by Day Line Chart */}
          <Card className="border py-4 lg:py-0 h-full">
            <CardHeader className="flex flex-col items-stretch border-b !p-0 lg:flex-row">
              <div className="flex flex-1 flex-col justify-center gap-1 px-6 pb-3 lg:pb-0">
                <CardTitle className="text-black">Events Over Time</CardTitle>
                <CardDescription className="text-gray-600">
                  Events in the last 30 days
                </CardDescription>
              </div>
              <div className="flex">
                <div className="flex flex-1 flex-col justify-center gap-1 border-t px-6 py-4 text-left lg:border-t-0 lg:border-l lg:px-8 lg:py-6">
                  <span className="text-gray-600 text-xs">Events</span>
                  <span className="text-lg leading-none font-bold lg:text-3xl text-black">
                    {totalEvents.events.toLocaleString()}
                  </span>
                </div>
              </div>
            </CardHeader>

            <CardContent className="px-2 lg:p-6 h-[320px] flex flex-col">
              {eventsChartData.length > 0 && (
                <div className="flex-1 flex justify-center items-center">
                  <ChartContainer
                    config={eventsChartConfig}
                    className="w-full h-[192px]"
                  >
                    <RechartsLineChart
                      accessibilityLayer
                      data={eventsChartData}
                      margin={{ left: 12, right: 12 }}
                    >
                      <XAxis
                        dataKey="date"
                        tickLine={false}
                        axisLine={{ stroke: '#000000' }}
                        tickMargin={8}
                        minTickGap={32}
                        tickFormatter={(value) => {
                          const date = new Date(value);
                          return date.toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric"
                          });
                        }}
                        stroke="#000000"
                        tick={{ fill: '#000000' }}
                      />
                      <ChartTooltip
                        content={
                          <ChartTooltipContent
                            className="w-[150px]"
                            nameKey="events"
                            labelFormatter={(value) => {
                              return new Date(value).toLocaleDateString("en-US", {
                                month: "short",
                                day: "numeric",
                                year: "numeric"
                              });
                            }}
                          />
                        }
                      />
                      <Line
                        dataKey="events"
                        type="monotone"
                        stroke="#4D96FF"
                        strokeWidth={2}
                        dot={false}
                      />
                    </RechartsLineChart>
                  </ChartContainer>
                  
                </div>
              )}
             {(!engagementStats || totalLeads === 0) && (
                <p className="text-gray-500 text-center py-8">No events available</p>
              )}

              <div className="flex flex-wrap gap-4 mt-4">
                {/* {eventsChartConfig.map((entry) => ( */}
                  <div className="flex items-center gap-2">
                    <span style={{ background: eventsChartConfig.events.color, width: 16, height: 16, display: 'inline-block', borderRadius: 4 }} />
                    <span className="text-sm text-black">{eventsChartConfig.events.label}</span>
                  </div>
                {/* ))} */}
              </div>

            </CardContent>
          </Card>

        </div>

        {/* Top Locations Table */}
        <Card className="border ">
          <CardHeader>
            <CardTitle className="text-black">Top 5 Lead Locations</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-black">City</TableHead>
                  <TableHead className="text-black">State</TableHead>
                  <TableHead className="text-black">Country</TableHead>
                  <TableHead className="text-black">Leads</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {topLocations.map((location, index) => (
                  <TableRow key={index}>
                    <TableCell className="text-black">{location.city}</TableCell>
                    <TableCell className="text-black">{location.state}</TableCell>
                    <TableCell className="text-black">{location.country}</TableCell>
                    <TableCell className="text-black">{location.count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {topLocations.length === 0 && (
              <p className="text-gray-500 text-center py-8">No location data available</p>
            )}
          </CardContent>
        </Card>

        {/* Recent Bulk Messages Table */}
        <Card className="border ">
          <CardHeader>
            <CardTitle className="text-black">Recent Messages</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-black">Subject</TableHead>
                  <TableHead className="text-black">Platform</TableHead>
                  <TableHead className="text-black">Total Leads</TableHead>
                  <TableHead className="text-black">Success</TableHead>
                  <TableHead className="text-black">Failed</TableHead>
                  <TableHead className="text-black">Sent At</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bulkMessages.map((message) => (
                  <TableRow key={message.id}>
                    <TableCell className="text-black">{message.subject || 'N/A'}</TableCell>
                    <TableCell className="text-black">{message.platform?.name || 'Unknown'}</TableCell>
                    <TableCell className="text-black">{message.total_leads}</TableCell>
                    <TableCell className="text-black">{message.success_count}</TableCell>
                    <TableCell className="text-black">{message.failed_count}</TableCell>
                    <TableCell className="text-black">{formatDate(message.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {bulkMessages.length === 0 && (
              <p className="text-gray-500 text-center py-8">No recent bulk messages</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}