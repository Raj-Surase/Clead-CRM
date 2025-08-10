// import { useState, useEffect } from "react";
// import { Button } from "@/components/ui/button";
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
// import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
// import { Mail, Users, MessageSquare, TrendingUp, Plus, Send, Settings } from "lucide-react";
// import { Link as RouterLink } from "react-router-dom";
// import { crmApi, IntegrationStatistics, OutreachMessage, Platform } from "@/lib/api";
// import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

// interface Campaign {
//   id: number;
//   name: string;
//   status: string;
//   total_leads: number;
// }

// interface MessageStats {
//   success_rate: number;
// }

// export default function Dashboard() {
//   const [isLoading, setIsLoading] = useState(true);
//   const [error, setError] = useState<string | null>(null);
//   const [stats, setStats] = useState({
//     totalCampaigns: 0,
//     totalMessages: 0,
//     leadsWithMessages: 0,
//     successRate: 0,
//   });
//   const [recentCampaigns, setRecentCampaigns] = useState<Campaign[]>([]);
//   const [recentEmails, setRecentEmails] = useState<any[]>([]);
//   const [messageStats, setMessageStats] = useState<any[]>([]);
//   const [engagementData, setEngagementData] = useState<any[]>([]);
//   const [leadMetrics, setLeadMetrics] = useState<any>(null);

//   useEffect(() => {
//     const fetchData = async () => {
//       try {
//         setIsLoading(true);
//         setError(null);

//         // Fetch campaigns
//         const campaigns = (await crmApi.getCampaigns()) as Campaign[];
//         // Fetch integration statistics
//         const integrationStats = await crmApi.getIntegrationStatistics() as IntegrationStatistics;
//         // Fetch message stats for success rate
//         const messageStats = await crmApi.getMessageStats() as MessageStats;
//         // Fetch recent emails
//         const emailsResponse = await crmApi.getOutreachMessages({ limit: 3, platform_id: 1, user_id: 1 });
//         setRecentEmails(emailsResponse.results || emailsResponse || []);

//         // Fetch outreach statistics for message status and engagement
//         const outreachStats = await crmApi.getOutreachStatistics();
//         // Only keep 'sent' and 'failed' statuses for the pie chart
//         const filteredMessageStats = (outreachStats.messageStats || []).filter((stat: any) => stat.status === 'sent' || stat.status === 'failed');
//         setMessageStats(filteredMessageStats);
//         setEngagementData(outreachStats.engagementData || []);

//         // Fetch lead metrics for total leads
//         const leadStats = await crmApi.getLeadStatisticsOverview();
//         setLeadMetrics(leadStats);

//         setStats({
//           totalCampaigns: campaigns.length,
//           totalMessages: integrationStats.total_messages,
//           leadsWithMessages: 0, // deprecated, not used
//           successRate: messageStats.success_rate,
//         });
//         setRecentCampaigns(campaigns.slice(0, 3));
//       } catch (err) {
//         setError(err instanceof Error ? err.message : 'An error occurred while fetching data');
//         console.error('Error fetching data:', err);
//       } finally {
//         setIsLoading(false);
//       }
//     };
//     fetchData();
//   }, []);

//   const PIE_COLORS = {
//     sent: "#3B82F6", // Blue
//     failed: "#EF4444", // Red
//     default: "#6B7280", // Gray
//   };

//   // Add formatDate helper for sent_at
//   const formatDate = (dateString: string) => {
//     return new Date(dateString).toLocaleString();
//   };

//   // Group recentEmails by bulk_group_id, similar to OutreachConversations
//   const groupedRecentEmails = (() => {
//     const grouped: any[] = [];
//     (recentEmails as OutreachMessage[]).forEach((message) => {
//       if (!message.bulk_group_id) {
//         grouped.push({
//           id: message.id.toString(),
//           bulk_group_id: null,
//           platform_id: message.platform_id,
//           platform: message.platform,
//           message_content: message.message_content,
//           subject: message.subject,
//           total_messages: 1,
//           sent_count: message.status === 'sent' ? 1 : 0,
//           failed_count: message.status === 'failed' ? 1 : 0,
//           delivered_count: message.status === 'delivered' ? 1 : 0,
//           read_count: message.status === 'read' ? 1 : 0,
//           sent_at: message.sent_at,
//           messages: [message],
//         });
//       } else {
//         const existingGroup = grouped.find(g => g.bulk_group_id === message.bulk_group_id);
//         if (existingGroup) {
//           existingGroup.total_messages++;
//           if (message.status === 'sent') existingGroup.sent_count++;
//           if (message.status === 'failed') existingGroup.failed_count++;
//           if (message.status === 'delivered') existingGroup.delivered_count++;
//           if (message.status === 'read') existingGroup.read_count++;
//           existingGroup.messages.push(message);
//         } else {
//           grouped.push({
//             id: `group-${message.bulk_group_id}`,
//             bulk_group_id: message.bulk_group_id,
//             platform_id: message.platform_id,
//             platform: message.platform,
//             message_content: message.message_content,
//             subject: message.subject,
//             total_messages: 1,
//             sent_count: message.status === 'sent' ? 1 : 0,
//             failed_count: message.status === 'failed' ? 1 : 0,
//             delivered_count: message.status === 'delivered' ? 1 : 0,
//             read_count: message.status === 'read' ? 1 : 0,
//             sent_at: message.sent_at,
//             messages: [message],
//           });
//         }
//       }
//     });
//     return grouped.sort((a, b) => new Date(b.sent_at).getTime() - new Date(a.sent_at).getTime()).slice(0, 3);
//   })();

//   if (error) {
//     return (
//       <div className="p-6 text-center">
//         <p className="text-red-500">Error: {error}</p>
//         <Button onClick={() => window.location.reload()} className="mt-4 bg-black text-white hover:bg-gray-800">
//           Retry
//         </Button>
//       </div>
//     );
//   }

//   if (isLoading) {
//     return (
//       <div className="p-6 text-center">
//         <p>Loading...</p>
//       </div>
//     );
//   }

//   return (
//     <div className="p-6  min-h-screen">
//       <div className="max-w-7xl mx-auto space-y-6">
//         {/* Header */}
//         <div className="flex justify-between items-center">
//           <div>
//             <h1 className="text-3xl font-bold text-black">Dashboard</h1>
//             <p className="text-gray-600">Manage your campaigns and conversations</p>
//           </div>
//           <div className="flex gap-3">
//             <Button asChild className="bg-black text-white hover:bg-gray-800">
//               <RouterLink to="/outreach/campaigns?create=true">
//                 <Plus className="w-4 h-4 mr-2" />
//                 Create Campaign
//               </RouterLink>
//             </Button>
//             {/* <Button asChild variant="outline" className="border-black text-black hover:bg-gray-100">
//               <RouterLink to="/outreach/send-message">
//                 <Send className="w-4 h-4 mr-2" />
//                 Send Message
//               </RouterLink>
//             </Button> */}
//             {/* <Button asChild variant="outline" className="border-black text-black hover:bg-gray-100">
//               <RouterLink to="/outreach/platforms">
//                 <Settings className="w-4 h-4 mr-2" />
//                 Manage Platforms
//               </RouterLink>
//             </Button> */}
//           </div>
//         </div>

//         {/* Statistics Cards */}
//         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
//           <Card className="border border-black">
//             <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//               <CardTitle className="text-sm font-medium text-black">Total Leads</CardTitle>
//               <Mail className="h-4 w-4 text-black" />
//             </CardHeader>
//             <CardContent>
//               <div className="text-2xl font-bold text-black">{leadMetrics?.total_leads ?? '-'}</div>
//             </CardContent>
//           </Card>
//           <Card className="border border-black">
//             <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//               <CardTitle className="text-sm font-medium text-black">Total Campaigns</CardTitle>
//               <Users className="h-4 w-4 text-black" />
//             </CardHeader>
//             <CardContent>
//               <div className="text-2xl font-bold text-black">{stats.totalCampaigns}</div>
//             </CardContent>
//           </Card>
//           <Card className="border border-black">
//             <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//               <CardTitle className="text-sm font-medium text-black">Total Messages</CardTitle>
//               <MessageSquare className="h-4 w-4 text-black" />
//             </CardHeader>
//             <CardContent>
//               <div className="text-2xl font-bold text-black">{stats.totalMessages.toLocaleString()}</div>
//             </CardContent>
//           </Card>
          
//           <Card className="border border-black">
//             <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//               <CardTitle className="text-sm font-medium text-black">Success Rate</CardTitle>
//               <TrendingUp className="h-4 w-4 text-black" />
//             </CardHeader>
//             <CardContent>
//               <div className="text-2xl font-bold text-black">{stats.successRate.toFixed(2)}%</div>
//             </CardContent>
//           </Card>
//         </div>

//         {/* Message Status Distribution and Lead Engagement Score */}
//         <div className="grid lg:grid-cols-2 gap-6">
//           {/* Message Status Pie Chart */}
//           <Card className="border border-black">
//             <CardHeader>
//               <CardTitle className="text-black">Message Status Distribution</CardTitle>
//               <CardDescription>Visual breakdown of sent and failed messages</CardDescription>
//             </CardHeader>
//             <CardContent>
//               {isLoading ? (
//                 <div className="text-center">Loading...</div>
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
//                         <Cell key={`cell-${index}`} fill={PIE_COLORS[entry.status] || PIE_COLORS.default} />
//                       ))}
//                     </Pie>
//                     <Tooltip />
//                   </PieChart>
//                 </ResponsiveContainer>
//               )}
//             </CardContent>
//           </Card>
//           {/* Lead Engagement Table */}
//           <Card className="border border-black">
//             <CardHeader>
//               <CardTitle className="text-black">Lead Engagement Scores</CardTitle>
//               <CardDescription>Engagement metrics for individual leads</CardDescription>
//             </CardHeader>
//             <CardContent>
//               {isLoading ? (
//                 <div className="text-center">Loading...</div>
//               ) : (
//                 <Table>
//                   <TableHeader>
//                     <TableRow>
//                       <TableHead className="text-black">Lead ID</TableHead>
//                       <TableHead className="text-black">Engagement Score</TableHead>
//                       <TableHead className="text-black">Messages Sent</TableHead>
//                       <TableHead className="text-black">Responses</TableHead>
//                       <TableHead className="text-black">Response Rate</TableHead>
//                     </TableRow>
//                   </TableHeader>
//                   <TableBody>
//                     {engagementData.map((lead: any) => (
//                       <TableRow key={lead.lead_id}>
//                         <TableCell className="text-black font-medium">{lead.lead_id}</TableCell>
//                         <TableCell className="text-black">
//                           <div className="flex items-center gap-2">
//                             <div className="w-16 bg-gray-200 rounded-full h-2">
//                               <div
//                                 className="bg-black h-2 rounded-full"
//                                 style={{ width: `${lead.engagement_score}%` }}
//                               ></div>
//                             </div>
//                             <span className="text-sm">{lead.engagement_score}</span>
//                           </div>
//                         </TableCell>
//                         <TableCell className="text-black">{lead.messages_sent}</TableCell>
//                         <TableCell className="text-black">{lead.responses}</TableCell>
//                         <TableCell className="text-black">
//                           {lead.messages_sent > 0 ? ((lead.responses / lead.messages_sent) * 100).toFixed(1) : "0.0"}%
//                         </TableCell>
//                       </TableRow>
//                     ))}
//                   </TableBody>
//                 </Table>
//               )}
//             </CardContent>
//           </Card>
//         </div>

//         {/* Recent Data Tables */}
//         <div className="grid lg:grid-cols-2 gap-6">
//           {/* Recent Campaigns */}
//           <Card className="border border-black">
//             <CardHeader>
//               <CardTitle className="text-black">Recent Campaigns</CardTitle>
//               <CardDescription>Latest campaign activities</CardDescription>
//             </CardHeader>
//             <CardContent>
//               <Table>
//                 <TableHeader>
//                   <TableRow>
//                     <TableHead className="text-black">Name</TableHead>
//                     <TableHead className="text-black">Status</TableHead>
//                     <TableHead className="text-black">Leads</TableHead>
//                   </TableRow>
//                 </TableHeader>
//                 <TableBody>
//                   {recentCampaigns.map((campaign) => (
//                     <TableRow key={campaign.id}>
//                       <TableCell className="text-black">
//                         <RouterLink
//                           to={`/outreach/campaigns/${campaign.id}`}
//                           className="hover:underline"
//                         >
//                           {campaign.name}
//                         </RouterLink>
//                       </TableCell>
//                       <TableCell>
//                         <span className={`px-2 py-1 rounded text-xs ${
//                           campaign.status === 'active' 
//                             ? 'bg-green-100 text-green-800' 
//                             : 'bg-yellow-100 text-yellow-800'
//                         }`}>
//                           {campaign.status}
//                         </span>
//                       </TableCell>
//                       <TableCell className="text-black">{campaign.total_leads}</TableCell>
//                     </TableRow>
//                   ))}
//                 </TableBody>
//               </Table>
//             </CardContent>
//           </Card>

//           {/* Recent Emails */}
//           <Card className="border border-black">
//             <CardHeader>
//               <CardTitle className="text-black">Recent Emails</CardTitle>
//               <CardDescription>Latest sent or failed outreach emails (grouped)</CardDescription>
//             </CardHeader>
//             <CardContent>
//               <Table>
//                 <TableHeader>
//                   <TableRow>
//                     <TableHead className="text-black">Subject</TableHead>
//                     <TableHead className="text-black">Content</TableHead>
//                     <TableHead className="text-black">Platform</TableHead>
//                     <TableHead className="text-black">Status</TableHead>
//                     <TableHead className="text-black">Total</TableHead>
//                     <TableHead className="text-black">Sent At</TableHead>
//                   </TableRow>
//                 </TableHeader>
//                 <TableBody>
//                   {groupedRecentEmails.map((group) => (
//                     <TableRow key={group.id}>
//                       <TableCell className="text-black">{group.subject || 'N/A'}</TableCell>
//                       <TableCell className="text-black font-medium max-w-xs whitespace-pre-wrap">{group.message_content}</TableCell>
//                       <TableCell className="text-black">{group.platform?.name || ''}</TableCell>
//                       <TableCell>
//                         {(() => {
//                           let status: 'sent' | 'failed' | 'delivered' | 'pending';
//                           let count: number;
//                           if (group.sent_count > group.failed_count) {
//                             status = 'sent';
//                             count = group.sent_count;
//                           } else if (group.failed_count > group.sent_count) {
//                             status = 'failed';
//                             count = group.failed_count;
//                           } else if (group.delivered_count > 0) {
//                             status = 'delivered';
//                             count = group.delivered_count;
//                           } else {
//                             status = 'pending';
//                             count = group.total_messages;
//                           }
//                           const statusStyles = {
//                             sent: 'bg-blue-100 text-blue-800',
//                             failed: 'bg-red-100 text-red-800',
//                             delivered: 'bg-green-100 text-green-800',
//                             pending: 'bg-purple-100 text-purple-800',
//                           };
//                           return (
//                             <span className={`px-2 py-1 rounded text-xs ${statusStyles[status]}`}>
//                               {`${status.charAt(0).toUpperCase() + status.slice(1)}`}
//                             </span>
//                           );
//                         })()}
//                       </TableCell>
//                       <TableCell className="text-black">{group.total_messages}</TableCell>
//                       <TableCell className="text-black">{formatDate(group.sent_at)}</TableCell>
//                     </TableRow>
//                   ))}
//                 </TableBody>
//               </Table>
//             </CardContent>
//           </Card>
//         </div>
//       </div>
//     </div>
//   );
// }