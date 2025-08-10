// import { useState, useEffect } from "react";
// import { Button } from "@/components/ui/button";
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
// import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
// import { Mail, Users, MessageSquare, TrendingUp, Plus, Send, Settings } from "lucide-react";
// import { Link } from "react-router-dom";
// // import { crmApi } from "@/lib/crmAPI";
// import { crmApi, IntegrationStatistics } from "@/lib/api";

// interface Campaign {
//   id: number;
//   name: string;
//   status: string;
//   total_leads: number;
// }

// interface MessageStats {
//   success_rate: number;
// }

// export default function OutreachOverview() {
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

//         // Update stats
//         setStats({
//           totalCampaigns: campaigns.length,
//           totalMessages: integrationStats.total_messages,
//           leadsWithMessages: integrationStats.leads_with_messages,
//           successRate: messageStats.success_rate,
//         });

//         // Update recent campaigns (taking first 3)
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

//   if (error) {
//     return (
//       <div className="p-6 text-center">
//         <p className="text-red-500">Error: {error}</p>
//         <Button 
//           onClick={() => window.location.reload()} 
//           className="mt-4 bg-black text-white hover:bg-gray-800"
//         >
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
//     <div className="p-8 min-h-screen">
//       <div className="space-y-6">
//         {/* Header */}
//         <div className="flex justify-between items-center">
//           <div>
//             <h1 className="text-3xl font-bold">Outreach Overview</h1>
//             <p className="text-muted-foreground">Manage your campaigns and conversations</p>
//           </div>
          
//           <div className="flex gap-3">
//             <Button asChild>
//               <Link to="/outreach/campaigns?create=true">
//                 <Plus className="w-4 h-4 mr-2" />
//                 Create Campaign
//               </Link>
//             </Button>
//             {/* <Button asChild variant="outline" className="border-black text-black hover:bg-gray-100">
//               <Link to="/outreach/send-message">
//                 <Send className="w-4 h-4 mr-2" />
//                 Send Message
//               </Link>
//             </Button> */}
//             {/* <Button asChild variant="outline" className="border-black text-black hover:bg-gray-100">
//               <Link to="/outreach/platforms">
//                 <Settings className="w-4 h-4 mr-2" />
//                 Manage Platforms
//               </Link>
//             </Button> */}
//           </div>
//         </div>

        

//         {/* Statistics Cards */}
//         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
//           <Card>
//             <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//               <CardTitle className="text-sm font-medium">Total Campaigns</CardTitle>
//               <Users className="h-4 w-4" />
//             </CardHeader>
//             <CardContent>
//               <div className="text-2xl font-bold">{stats.totalCampaigns}</div>
//             </CardContent>
//           </Card>

//           <Card>
//             <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//               <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
//               <MessageSquare className="h-4 w-4" />
//             </CardHeader>
//             <CardContent>
//               <div className="text-2xl font-bold">{stats.totalMessages.toLocaleString()}</div>
//             </CardContent>
//           </Card>

//           <Card>
//             <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//               <CardTitle className="text-sm font-medium">Leads with Messages</CardTitle>
//               <Mail className="h-4 w-4" />
//             </CardHeader>
//             <CardContent>
//               <div className="text-2xl font-bold">{stats.leadsWithMessages}</div>
//             </CardContent>
//           </Card>

//           <Card>
//             <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
//               <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
//               <TrendingUp className="h-4 w-4" />
//             </CardHeader>
//             <CardContent>
//               <div className="text-2xl font-bold">{stats.successRate.toFixed(2)}%</div>
//             </CardContent>
//           </Card>
//         </div>

//         {/* Recent Data Tables */}
//         <div className="grid lg:grid-cols-2 gap-6">
//           {/* Recent Campaigns */}
//           <Card>
//             <CardHeader>
//               <CardTitle>Recent Campaigns</CardTitle>
//               <CardDescription>Latest campaign activities</CardDescription>
//             </CardHeader>
//             <CardContent>
//               <Table>
//                 <TableHeader>
//                   <TableRow>
//                     <TableHead>Name</TableHead>
//                     <TableHead>Status</TableHead>
//                     <TableHead>Leads</TableHead>
//                   </TableRow>
//                 </TableHeader>
//                 <TableBody>
//                   {recentCampaigns.map((campaign) => (
//                     <TableRow key={campaign.id} className="cursor-pointer hover:bg-accent/50">
//                       <TableCell>
//                         <Link 
//                           to={`/outreach/campaigns/${campaign.id}`}
//                           className="hover:underline"
//                         >
//                           {campaign.name}
//                         </Link>
//                       </TableCell>
//                       <TableCell>
//                         <span className={`px-3 py-1 rounded-full text-xs font-medium ${
//                           campaign.status === 'active' 
//                             ? 'bg-green-100 text-green-800' 
//                             : campaign.status === 'paused'
//                             ? 'bg-yellow-100 text-yellow-800'
//                             : 'bg-gray-100 text-gray-800'
//                         }`}>
//                           {campaign.status}
//                         </span>
//                       </TableCell>
//                       <TableCell>{campaign.total_leads}</TableCell>
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
//               <CardDescription>Latest sent or failed outreach emails</CardDescription>
//             </CardHeader>
//             <CardContent>
//               <Table>
//                 <TableHeader>
//                   <TableRow>
//                     <TableHead className="text-black">Content</TableHead>
//                     <TableHead className="text-black">Lead ID</TableHead>
//                     <TableHead className="text-black">Platform</TableHead>
//                     <TableHead className="text-black">Status</TableHead>
//                     {/* <TableHead className="text-black">Sent At</TableHead> */}
//                   </TableRow>
//                 </TableHeader>
//                 <TableBody>
//                   {recentEmails.map((email) => (
//                     <TableRow key={email.id}>
//                       <TableCell className="text-black font-medium max-w-xs whitespace-pre-wrap">{email.message_content}</TableCell>
//                       <TableCell className="text-black">{email.lead_id}</TableCell>
//                       <TableCell className="text-black">{email.platform?.name || ''}</TableCell>
//                       <TableCell>
//                         <span className={`px-2 py-1 rounded text-xs ${
//                           email.status === 'sent' 
//                             ? 'bg-blue-100 text-blue-800' 
//                             : 'bg-red-100 text-red-800'
//                         }`}>
//                           {email.status}
//                         </span>
//                       </TableCell>
//                       {/* <TableCell className="text-black">{email.sent_at ? new Date(email.sent_at).toLocaleString() : 'N/A'}</TableCell> */}
//                     </TableRow>
//                   ))}
//                 </TableBody>
//               </Table>
//             </CardContent>
//           </Card>
          
//         </div>
//         {/* Email App Password Guide */}
//         {/* <Card className="border-2 border-yellow-200 bg-yellow-50">
//           <CardHeader>
//             <CardTitle className="text-black flex items-center gap-2">
//               <Mail className="w-5 h-5" />
//               Email Platform Setup Guide
//             </CardTitle>
//             <CardDescription>
//               To connect your email platforms, you'll need to generate app-specific passwords
//             </CardDescription>
//           </CardHeader>
//           <CardContent className="space-y-4">
//             <div className="grid md:grid-cols-2 gap-4">
//               <div className="space-y-2">
//                 <h4 className="font-semibold text-black">Gmail Setup:</h4>
//                 <ol className="list-decimal list-inside text-sm text-gray-700 space-y-1">
//                   <li>Go to Google Account settings</li>
//                   <li>Enable 2-factor authentication</li>
//                   <li>Navigate to Security → App passwords</li>
//                   <li>Generate a new app password for "Mail"</li>
//                   <li>Use this password in platform connection</li>
//                 </ol>
//               </div>
//               <div className="space-y-2">
//                 <h4 className="font-semibold text-black">Outlook Setup:</h4>
//                 <ol className="list-decimal list-inside text-sm text-gray-700 space-y-1">
//                   <li>Go to Microsoft Account security</li>
//                   <li>Enable 2-factor authentication</li>
//                   <li>Create an app password</li>
//                   <li>Select "Mail" as the app type</li>
//                   <li>Copy the generated password</li>
//                 </ol>
//               </div>
//             </div>
//             <Button asChild className="bg-black text-white hover:bg-gray-800">
//               <Link to="/outreach/platforms">
//                 Connect Email Platform
//               </Link>
//             </Button>
//           </CardContent>
//         </Card> */}
//       </div>
//     </div>
//   );
// }
