import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Search,
  LogOut,
  Database,
  TrendingUp,
  ShoppingCart,
  MapPin,
  Users,
  BarChart3,
} from "lucide-react";

const suggestedQuestions = [
  {
    icon: TrendingUp,
    question: "Show total sales by category",
    category: "Sales Analytics",
  },
  {
    icon: ShoppingCart,
    question: "Top 5 products by transaction amount",
    category: "Product Performance",
  },
  {
    icon: MapPin,
    question: "Which store has the highest sales?",
    category: "Store Analysis",
  },
  {
    icon: Users,
    question: "Show inventory levels by store",
    category: "Inventory Insights",
  },
  {
    icon: BarChart3,
    question: "Compare sales by category for week 29",
    category: "Weekly Analytics",
  },
];

const Home = () => {
  const [query, setQuery] = useState("");
  const [username, setUsername] = useState("User");
  const navigate = useNavigate();

  useEffect(() => {
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    if (!isLoggedIn) {
      navigate("/");
      return;
    }
    const storedUsername = localStorage.getItem("username");
    if (storedUsername) {
      setUsername(storedUsername);
    }
  }, [navigate]);

  const handleSearch = (searchQuery: string) => {
    if (searchQuery.trim()) {
      navigate(`/results?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("username");
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
              <Database className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-bold text-foreground text-lg">Text2SQL</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-sm font-medium text-primary-foreground">
                {username.charAt(0).toUpperCase()}
              </div>
              <span className="text-sm text-foreground hidden sm:block">{username}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-muted-foreground hover:text-foreground"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-16 md:py-24">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-foreground">
            Ask your data <span className="text-primary">anything</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Transform natural language questions into SQL queries instantly.
            No coding required.
          </p>
        </div>

        {/* Search Box */}
        <div className="mb-16">
          <div className="relative bg-card rounded-xl shadow-lg border p-2">
            <div className="relative flex items-center">
              <Search className="absolute left-4 w-5 h-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Ask a question about your data..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch(query)}
                className="h-14 pl-12 pr-32 text-base border-0 focus-visible:ring-0"
              />
              <Button
                size="lg"
                className="absolute right-2"
                onClick={() => handleSearch(query)}
              >
                Generate SQL
              </Button>
            </div>
          </div>
        </div>

        {/* Suggested Questions */}
        <div>
          <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-6 text-center">
            Try These Questions
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {suggestedQuestions.map((item, index) => (
              <button
                key={index}
                onClick={() => handleSearch(item.question)}
                className="bg-card hover:bg-accent border rounded-xl p-4 text-left transition-colors group"
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                    <item.icon className="w-5 h-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground group-hover:text-primary transition-colors">
                      {item.question}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">{item.category}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-16 text-center">
          <p className="text-sm text-muted-foreground">
            Connected to <span className="font-medium text-foreground">causal_inference</span> database
          </p>
        </div>
      </main>
    </div>
  );
};

export default Home;
