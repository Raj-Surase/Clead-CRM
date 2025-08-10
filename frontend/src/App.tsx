import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { FloatingSidebar } from "@/components/FloatingSidebar";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute, AuthRoute, OnboardingRoute } from "@/components/ProtectedRoute";
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import NotFound from "./pages/NotFound";
import LeadsModule from "./pages/leads/LeadsModule";
import LeadDetails from "./pages/leads/LeadDetails";
import CalendarModule from "./pages/calendar/CalendarModule";
import EventDetails from "./pages/calendar/EventDetails";
import LeadEvents from "./pages/calendar/LeadEvents";
import OutreachCampaigns from "./pages/outreach/OutreachCampaigns";
import CampaignDetails from "./pages/outreach/CampaignDetails";
import OutreachTemplates from "./pages/outreach/OutreachTemplates";
import OutreachConversations from "./pages/outreach/OutreachConversations";
import ConversationDetails from "./pages/outreach/ConversationDetails";
import OutreachPlatforms from "./pages/outreach/OutreachPlatforms";
import SendMessage from "./pages/outreach/SendMessage";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import ForgotPassword from "./pages/auth/ForgotPassword";
import PersonalInfo from "./pages/onboarding/PersonalInfo";
import CompanyInfo from "./pages/onboarding/CompanyInfo";
import Profile from "./pages/Profile";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            {/* Auth Routes */}
            <Route path="/login" element={<AuthRoute><Login /></AuthRoute>} />
            <Route path="/register" element={<AuthRoute><Register /></AuthRoute>} />
            <Route path="/forgot-password" element={<AuthRoute><ForgotPassword /></AuthRoute>} />
            
            {/* Onboarding Routes */}
            <Route path="/onboarding" element={<OnboardingRoute><Navigate to="/onboarding/personal" replace /></OnboardingRoute>} />
            <Route path="/onboarding/personal" element={<OnboardingRoute><PersonalInfo /></OnboardingRoute>} />
            <Route path="/onboarding/company" element={<OnboardingRoute><CompanyInfo /></OnboardingRoute>} />
            
            {/* Protected App Routes */}
            <Route path="/" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><Index /></main></div></ProtectedRoute>} />
            <Route path="/dashboard" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><Dashboard /></main></div></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><Profile /></main></div></ProtectedRoute>} />
            
            {/* Leads Routes */}
            <Route path="/leads" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><LeadsModule /></main></div></ProtectedRoute>} />
            <Route path="/leads/:leadId" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><LeadDetails /></main></div></ProtectedRoute>} />
            
            {/* Calendar Routes */}
            <Route path="/calendar" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><CalendarModule /></main></div></ProtectedRoute>} />
            <Route path="/calendar/events/:eventId" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><EventDetails /></main></div></ProtectedRoute>} />
            <Route path="/calendar/leads/:leadId" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><LeadEvents /></main></div></ProtectedRoute>} />

            {/* Outreach Routes */}
            <Route path="/outreach/campaigns" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><OutreachCampaigns /></main></div></ProtectedRoute>} />
            <Route path="/outreach/campaigns/:campaignId" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><CampaignDetails /></main></div></ProtectedRoute>} />
            <Route path="/outreach/templates" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><OutreachTemplates /></main></div></ProtectedRoute>} />
            <Route path="/outreach/emails" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><OutreachConversations /></main></div></ProtectedRoute>} />
            <Route path="/outreach/conversations/:conversationId" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><ConversationDetails /></main></div></ProtectedRoute>} />
            <Route path="/outreach/platforms" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><OutreachPlatforms /></main></div></ProtectedRoute>} />
            <Route path="/outreach/send" element={<ProtectedRoute><div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20"><FloatingSidebar /><main className="md:ml-20 px-4 md:px-8 pt-20 md:pt-8"><SendMessage /></main></div></ProtectedRoute>} />

            {/* Not Found Route */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;