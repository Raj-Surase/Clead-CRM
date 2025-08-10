import { Calendar, History, BarChart3, Mail, Users, MessageSquare, Search, Home, Menu, X, Settings, Globe } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useIsMobile } from "@/hooks/use-mobile";
import { useState } from "react";

const modules = [
  { title: "Dashboard", url: "/dashboard", icon: Home },
  { title: "Leads", url: "/leads", icon: BarChart3 },
  { title: "Templates", url: "/outreach/templates", icon: MessageSquare },
  { title: "Platforms", url: "/outreach/platforms", icon: Globe },
  { title: "Campaigns", url: "/outreach/campaigns", icon: Users },
  { title: "Emails", url: "/outreach/emails", icon: Search },
  { title: "Calendar", url: "/calendar", icon: Calendar },
  { title: "Profile", url: "/profile", icon: Settings },
];

export function FloatingSidebar() {
  const location = useLocation();
  const isMobile = useIsMobile();
  const [isOpen, setIsOpen] = useState(false);

  if (isMobile) {
    return (
      <>
        {/* Mobile Menu Button */}
        <div className="fixed top-4 left-4 z-50">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-3 bg-card/80 backdrop-blur-xl rounded-full shadow-glass border border-border/50 text-foreground hover:bg-accent/50 transition-all duration-300"
          >
            {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile Menu Overlay */}
        {isOpen && (
          <div className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm" onClick={() => setIsOpen(false)}>
            <div className="fixed top-20 left-4 right-4">
              <div className="flex flex-col gap-2 p-4 bg-card/95 backdrop-blur-xl rounded-3xl shadow-glass border border-border/50">
                {modules.map((item) => {
                  const isActive = location.pathname === item.url;
                  return (
                    <Link
                      key={item.title}
                      to={item.url}
                      onClick={() => setIsOpen(false)}
                      className={cn(
                        "flex items-center gap-3 p-3 rounded-2xl transition-all duration-300",
                        isActive 
                          ? "bg-gradient-primary text-primary-foreground shadow-medium" 
                          : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                      )}
                    >
                      <item.icon className="w-5 h-5" />
                      <span className="text-sm font-medium">{item.title}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Desktop/Tablet version
  return (
    <div className="fixed left-6 top-1/2 -translate-y-1/2 z-50 hidden md:block">
      <div className="flex flex-col gap-3 p-4 bg-card/80 backdrop-blur-xl rounded-3xl shadow-glass border border-border/50">
        {modules.map((item) => {
          const isActive = location.pathname === item.url;
          return (
            <Link
              key={item.title}
              to={item.url}
              className={cn(
                "group relative p-3 rounded-full transition-all duration-300 hover:scale-110",
                isActive 
                  ? "bg-gradient-primary text-primary-foreground shadow-medium" 
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              <item.icon className="w-5 h-5" />
              
              {/* Tooltip */}
              <div className="absolute left-full ml-4 px-3 py-2 bg-popover/95 backdrop-blur-sm text-popover-foreground text-sm rounded-xl shadow-medium opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
                {item.title}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}