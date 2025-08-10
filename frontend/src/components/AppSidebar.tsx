
import { Calendar, Upload, History, Search, Settings, BarChart3, Mail, Bot, MessageSquare, Users, Zap, Globe, Send, TrendingUp, Home, CalendarCog, CalendarCheck } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from "@/components/ui/sidebar";
import { Link, useLocation } from "react-router-dom";

const modules = [
  {
    title: "Overview",
    items: [
      { title: "Dashboard", url: "/dashboard", icon: Home },
    ],
  },
  {
    title: "Lead Parser",
    items: [
      { title: "Overview", url: "/leads", icon: BarChart3 },
      // { title: "Upload Files", url: "/leads/upload", icon: Upload },
      { title: "History", url: "/leads/history", icon: History },
    ],
  },
  {
    title: "Outreach",
    items: [
      // { title: "Overview", url: "/outreach", icon: Mail },
      { title: "Campaigns", url: "/outreach/campaigns", icon: Users },
      { title: "Templates", url: "/outreach/templates", icon: MessageSquare },
      { title: "Emails", url: "/outreach/emails", icon: Search },
      // { title: "Platforms", url: "/outreach/platforms", icon: Globe },
      // { title: "Send Message", url: "/outreach/send-message", icon: Send },
      // { title: "Statistics", url: "/outreach/statistics", icon: TrendingUp },
    ],
  },
  {
    title: "Calendar",
    items: [
      { title: "Events", url: "/calendar", icon: Calendar },
      // { title: "Create Event", url: "/calendar/events/create", icon: CalendarCog },
      // { title: "Check Availability", url: "/calendar/availability", icon: CalendarCheck },
    ],
  },
];

export function AppSidebar() {
  const location = useLocation();

  return (
    <Sidebar className="border-r border-gray-200 bg-gradient-to-b from-white to-gray-50">
      <SidebarHeader className="border-b border-gray-200 p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              AI Sales Agency
            </h1>
            <p className="text-xs text-gray-500">Next-Gen Platform</p>
          </div>
        </div>
      </SidebarHeader>
      
      <SidebarContent className="p-4">
        {modules.map((module) => (
          <SidebarGroup key={module.title}>
            <SidebarGroupLabel className="text-gray-700 font-semibold mb-2">
              {module.title}
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {module.items.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      className={`transition-all duration-300 rounded-lg hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 border border-transparent ${
                        location.pathname === item.url
                          ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white border-transparent shadow-md"
                          : "text-gray-700 hover:border-gray-200 hover:text-gray-900"
                      }`}
                    >
                      <Link to={item.url} className="flex items-center gap-3 w-full">
                        <item.icon className="w-4 h-4" />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
      
      <SidebarFooter className="border-t border-gray-200 p-4">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
          API Status: Healthy
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
