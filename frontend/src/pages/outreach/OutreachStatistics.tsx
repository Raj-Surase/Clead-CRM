// import { useState, useEffect } from "react";
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
// import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
// import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
// import { MessageSquare, Users, TrendingUp, Mail, Target, CheckCircle, Loader2 } from "lucide-react";
// import { Button } from "@/components/ui/button";
// import { toast } from "@/hooks/use-toast";
// import { crmApi } from "@/lib/crmAPI";

// // Define interfaces to match API response
// interface Statistics {
//   total_messages: number;
//   total_campaigns: number;
//   total_conversations: number;
//   leads_with_events_percentage: number;
//   response_rate: number;
//   conversion_rate: number;
// }

// interface MessageStat {
//   name: string;
//   value: number;
//   status: string;
// }

// interface EngagementData {
//   lead_id: string;
//   engagement_score: number;
//   messages_sent: number;
//   responses: number;
// }

// export default function OutreachStatistics() {
//   const [statistics, setStatistics] = useState<Statistics | null>(null);
//   const [messageStats, setMessageStats] = useState<MessageStat[]>([]);
//   const [engagementData, setEngagementData] = useState<EngagementData[]>([]);
//   const [platformFilter, setPlatformFilter] = useState<string>("all");
//   const [userFilter, setUserFilter] = useState<string>("all");
//   const [isLoading, setIsLoading] = useState<boolean>(true);
//   const [error, setError] = useState<string | null>(null);

//   useEffect(() => {
//     const fetchData = async () => {
//       try {
//         setIsLoading(true);
//         setError(null);

//         // Prepare query parameters for filters
//         const params: { platform_id?: number; user_id?: number } = {};
//         if (platformFilter !== "all") {
//           params.platform_id = parseInt(platformFilter);
//         }
//         if (userFilter !== "all") {
//           params.user_id = parseInt(userFilter.replace("user", ""));
//         }

//         // Fetch outreach statistics
//         const response = await crmApi.getOutreachStatistics(params);

//         setStatistics(response.statistics);
//         setMessageStats(response.messageStats);
//         setEngagementData(response.engagementData);
//       } catch (err) {
//         const errorMessage = err instanceof Error ? err.message : "Failed to fetch outreach statistics";
//         setError(errorMessage);
//         toast({
//           variant: "destructive",
//           title: "Error",
//           description: errorMessage,
//         });
//       } finally {
//         setIsLoading(false);
//       }
//     };

//     fetchData();
//   }, [platformFilter, userFilter]);

//   // Colors for message status pie chart
//   const COLORS = {
//     failed: "#EF4444", // Red for Failed
//     sent: "#3B82F6", // Blue for Sent
//     delivered: "#10B981", // Green for Delivered
//     opened: "#F59E0B", // Yellow for Opened
//     replied: "#8B5CF6", // Purple for Replied
//     default: "#6B7280", // Gray for empty/unknown status
//   };

//   if (error) {
//     return (
//       <div className="p-6 text-center">
//         <p className="text-red-500">Error: {error}</p>
//         <Button
//           onClick={() => window.location.reload()}
//           className="mt-4 bg-black text-white hover:bg-gray-800"
//           disabled={isLoading}
//         >
//           {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
//           Retry
//         </Button>
//       </div>
//     );
//   }

//   return (
//     <div className="p-6  min-h-screen">
//       <div className="max-w-7xl mx-auto space-y-6">
//         {/* Header */}
//         <div className="flex justify-between items-center">
//           <div>
//             <h1 className="text-3xl font-bold text-black">Outreach Statistics</h1>
//             <p className="text-gray-600">Analyze your outreach performance and engagement</p>
//           </div>
//           {/* <div className="flex gap-3">
//             <Select value={platformFilter} onValueChange={setPlatformFilter} disabled={isLoading}>
//               <SelectTrigger className="w-48 border-black">
//                 <SelectValue placeholder="Filter by platform" />
//               </SelectTrigger>
//               <SelectContent className=" border-black">
//                 <SelectItem value="all">All Platforms</SelectItem>
//                 <SelectItem value="1">Email</SelectItem>
//                 <SelectItem value="2">WhatsApp</SelectItem>
//                 <SelectItem value="3">Facebook</SelectItem>
//               </SelectContent>
//             </Select>
//             <Select value={userFilter} onValueChange={setUserFilter} disabled={isLoading}>
//               <SelectTrigger className="w-48 border-black">
//                 <SelectValue placeholder="Filter by user" />
//               </SelectTrigger>
//               <SelectContent className=" border-black">
//                 <SelectItem value="all">All Users</SelectItem>
//                 <SelectItem value="user1">John Doe</SelectItem>
//                 <SelectItem value="user2">Jane Smith</SelectItem>
//               </SelectContent>
//             </Select>
//           </div> */}
//         </div>

//         {/* Overview Metrics */}
//         {isLoading ? (
//           <div className="text-center">
//             <Loader2 className="h-8 w-8 animate-spin mx-auto" />
//           </div>
//         ) : statistics ? (
//           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-6">
//             <Card className="border border-black">
//               <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//                 <CardTitle className="text-sm font-medium text-black">Total Messages</CardTitle>
//                 <MessageSquare className="h-4 w-4 text-black" />
//               </CardHeader>
//               <CardContent>
//                 <div className="text-2xl font-bold text-black">{statistics.total_messages.toLocaleString()}</div>
//               </CardContent>
//             </Card>
//             <Card className="border border-black">
//               <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//                 <CardTitle className="text-sm font-medium text-black">Campaigns</CardTitle>
//                 <Target className="h-4 w-4 text-black" />
//               </CardHeader>
//               <CardContent>
//                 <div className="text-2xl font-bold text-black">{statistics.total_campaigns}</div>
//               </CardContent>
//             </Card>
//             {/* <Card className="border border-black">
//               <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//                 <CardTitle className="text-sm font-medium text-black">Conversations</CardTitle>
//                 <Mail className="h-4 w-4 text-black" />
//               </CardHeader>
//               <CardContent>
//                 <div className="text-2xl font-bold text-black">{statistics.total_conversations}</div>
//               </CardContent>
//             </Card> */}
//             <Card className="border border-black">
//               <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//                 <CardTitle className="text-sm font-medium text-black">Leads with Events</CardTitle>
//                 <Users className="h-4 w-4 text-black" />
//               </CardHeader>
//               <CardContent>
//                 <div className="text-2xl font-bold text-black">{statistics.leads_with_events_percentage.toFixed(1)}%</div>
//               </CardContent>
//             </Card>
//             {/* <Card className="border border-black">
//               <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//                 <CardTitle className="text-sm font-medium text-black">Response Rate</CardTitle>
//                 <TrendingUp className="h-4 w-4 text-black" />
//               </CardHeader>
//               <CardContent>
//                 <div className="text-2xl font-bold text-black">{statistics.response_rate.toFixed(1)}%</div>
//               </CardContent>
//             </Card> */}
//             {/* <Card className="border border-black">
//               <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//                 <CardTitle className="text-sm font-medium text-black">Conversion Rate</CardTitle>
//                 <CheckCircle className="h-4 w-4 text-black" />
//               </CardHeader>
//               <CardContent>
//                 <div className="text-2xl font-bold text-black">{statistics.conversion_rate.toFixed(1)}%</div>
//               </CardContent>
//             </Card> */}
//           </div>
//         ) : null}

//         {/* Charts */}
//         <div className="grid lg:grid-cols-2 gap-6">
//           {/* Message Statistics Bar Chart */}
//           <Card className="border border-black">
//             <CardHeader>
//               <CardTitle className="text-black">Message Statistics</CardTitle>
//               <CardDescription>Breakdown of message status</CardDescription>
//             </CardHeader>
//             <CardContent>
//               {isLoading ? (
//                 <div className="text-center">
//                   <Loader2 className="h-8 w-8 animate-spin mx-auto" />
//                 </div>
//               ) : (
//                 <ResponsiveContainer width="100%" height={300}>
//                   <BarChart data={messageStats}>
//                     <CartesianGrid strokeDasharray="3 3" />
//                     <XAxis dataKey="name" />
//                     <YAxis />
//                     <Tooltip />
//                     <Bar dataKey="value" fill="#000000" />
//                   </BarChart>
//                 </ResponsiveContainer>
//               )}
//             </CardContent>
//           </Card>

//           {/* Message Status Pie Chart */}
//           <Card className="border border-black">
//             <CardHeader>
//               <CardTitle className="text-black">Message Status Distribution</CardTitle>
//               <CardDescription>Visual breakdown of message outcomes</CardDescription>
//             </CardHeader>
//             <CardContent>
//               {isLoading ? (
//                 <div className="text-center">
//                   <Loader2 className="h-8 w-8 animate-spin mx-auto" />
//                 </div>
//               ) : (
//                 <ResponsiveContainer width="100%" height={300}>
//                   <PieChart>
//                     <Pie
//                       data={messageStats}
//                       cx="50%"
//                       cy="50%"
//                       labelLine={false}
//                       label={({ name, percent }) => `${name || "Unknown"} ${(percent * 100).toFixed(0)}%`}
//                       outerRadius={80}
//                       dataKey="value"
//                     >
//                       {messageStats.map((entry, index) => (
//                         <Cell key={`cell-${index}`} fill={COLORS[entry.status] || COLORS.default} />
//                       ))}
//                     </Pie>
//                     <Tooltip />
//                   </PieChart>
//                 </ResponsiveContainer>
//               )}
//             </CardContent>
//           </Card>
//         </div>

//         {/* Lead Engagement Table */}
//         <Card className="border border-black">
//           <CardHeader>
//             <CardTitle className="text-black">Lead Engagement Scores</CardTitle>
//             <CardDescription>Engagement metrics for individual leads</CardDescription>
//           </CardHeader>
//           <CardContent>
//             {isLoading ? (
//               <div className="text-center">
//                 <Loader2 className="h-8 w-8 animate-spin mx-auto" />
//               </div>
//             ) : (
//               <Table>
//                 <TableHeader>
//                   <TableRow>
//                     <TableHead className="text-black">Lead ID</TableHead>
//                     <TableHead className="text-black">Engagement Score</TableHead>
//                     <TableHead className="text-black">Messages Sent</TableHead>
//                     <TableHead className="text-black">Responses</TableHead>
//                     <TableHead className="text-black">Response Rate</TableHead>
//                   </TableRow>
//                 </TableHeader>
//                 <TableBody>
//                   {engagementData.map((lead) => (
//                     <TableRow key={lead.lead_id}>
//                       <TableCell className="text-black font-medium">{lead.lead_id}</TableCell>
//                       <TableCell className="text-black">
//                         <div className="flex items-center gap-2">
//                           <div className="w-16 bg-gray-200 rounded-full h-2">
//                             <div
//                               className="bg-black h-2 rounded-full"
//                               style={{ width: `${lead.engagement_score}%` }}
//                             ></div>
//                           </div>
//                           <span className="text-sm">{lead.engagement_score}</span>
//                         </div>
//                       </TableCell>
//                       <TableCell className="text-black">{lead.messages_sent}</TableCell>
//                       <TableCell className="text-black">{lead.responses}</TableCell>
//                       <TableCell className="text-black">
//                         {lead.messages_sent > 0 ? ((lead.responses / lead.messages_sent) * 100).toFixed(1) : "0.0"}%
//                       </TableCell>
//                     </TableRow>
//                   ))}
//                 </TableBody>
//               </Table>
//             )}
//           </CardContent>
//         </Card>
//       </div>
//     </div>
//   );
// }