import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Users, Brain, Activity, Shield, Edit, Trash2, UserCheck, UserX } from "lucide-react";
import { ParticleBackground } from "@/components/layout/ParticleBackground";
import { GlassCard } from "@/components/ui/GlassCard";
import { NeonButton } from "@/components/ui/NeonButton";
import { useAuth } from "@/hooks/useAuth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  status: "active" | "disabled";
}

export default function AdminPanel() {
  const { user, loading: authLoading } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [action, setAction] = useState<string | null>(null);
  const [confidenceThreshold, setConfidenceThreshold] = useState([75]);
  const [humanOverride, setHumanOverride] = useState(true);
  const [aiUptime, setAiUptime] = useState(98);
  const [alertHealth, setAlertHealth] = useState(95);

  useEffect(() => {
    // Mock users
    const mockUsers: User[] = [
      { id: "1", name: "John Doe", email: "john@example.com", role: "admin", status: "active" },
      { id: "2", name: "Jane Smith", email: "jane@example.com", role: "compliance_officer", status: "active" },
      { id: "3", name: "Bob Johnson", email: "bob@example.com", role: "auditor", status: "disabled" },
    ];
    setUsers(mockUsers);
  }, []);

  const handleUserAction = (user: User, actionType: string) => {
    setSelectedUser(user);
    setAction(actionType);
  };

  const confirmAction = () => {
    if (!selectedUser || !action) return;
    if (action === "delete") {
      setUsers(prev => prev.filter(u => u.id !== selectedUser.id));
    } else if (action === "disable") {
      setUsers(prev => prev.map(u => u.id === selectedUser.id ? { ...u, status: "disabled" } : u));
    } else if (action === "enable") {
      setUsers(prev => prev.map(u => u.id === selectedUser.id ? { ...u, status: "active" } : u));
    }
    setAction(null);
    setSelectedUser(null);
  };

  const updateRole = (userId: string, newRole: string) => {
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: newRole } : u));
  };

  if (authLoading) return <div>Loading...</div>;
  if (!user || user.role !== "admin") {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <GlassCard className="p-8 text-center">
          <Shield className="h-12 w-12 mx-auto mb-4 text-destructive" />
          <h2 className="text-xl font-bold mb-2">Access Denied</h2>
          <p className="text-muted-foreground">Admin privileges required to access this panel.</p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      <ParticleBackground />
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-2xl md:text-3xl font-display font-bold text-glow">
            Admin & Governance Panel
          </h1>
          <p className="text-muted-foreground text-sm">
            System administration and AI governance controls
          </p>
        </motion.div>

        {/* Tabs */}
        <Tabs defaultValue="users" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="users" className="relative">
              <Users className="h-4 w-4 mr-2" />
              User Management
            </TabsTrigger>
            <TabsTrigger value="ai" className="relative">
              <Brain className="h-4 w-4 mr-2" />
              AI Governance
            </TabsTrigger>
            <TabsTrigger value="health" className="relative">
              <Activity className="h-4 w-4 mr-2" />
              System Health
            </TabsTrigger>
          </TabsList>

          {/* User Management */}
          <TabsContent value="users">
            <GlassCard className="p-6">
              <h2 className="text-lg font-semibold mb-4">User Management</h2>
              <div className="space-y-4">
                {users.map((u) => (
                  <motion.div
                    key={u.id}
                    className="flex items-center justify-between p-4 bg-muted/20 rounded-lg"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <div className="flex items-center gap-4">
                      <div>
                        <p className="font-medium">{u.name}</p>
                        <p className="text-sm text-muted-foreground">{u.email}</p>
                      </div>
                      <Badge variant={u.status === "active" ? "default" : "secondary"}>
                        {u.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Select value={u.role} onValueChange={(value) => updateRole(u.id, value)}>
                        <SelectTrigger className="w-40">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="admin">Admin</SelectItem>
                          <SelectItem value="compliance_officer">Compliance Officer</SelectItem>
                          <SelectItem value="auditor">Auditor</SelectItem>
                          <SelectItem value="manager">Manager</SelectItem>
                        </SelectContent>
                      </Select>
                      {u.status === "active" ? (
                        <NeonButton
                          variant="outline"
                          size="sm"
                          onClick={() => handleUserAction(u, "disable")}
                        >
                          <UserX className="h-4 w-4" />
                        </NeonButton>
                      ) : (
                        <NeonButton
                          variant="outline"
                          size="sm"
                          onClick={() => handleUserAction(u, "enable")}
                        >
                          <UserCheck className="h-4 w-4" />
                        </NeonButton>
                      )}
                      <NeonButton
                        variant="destructive"
                        size="sm"
                        onClick={() => handleUserAction(u, "delete")}
                      >
                        <Trash2 className="h-4 w-4" />
                      </NeonButton>
                    </div>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </TabsContent>

          {/* AI Governance */}
          <TabsContent value="ai">
            <GlassCard className="p-6">
              <h2 className="text-lg font-semibold mb-4">AI Governance Controls</h2>
              <div className="space-y-6">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    AI Confidence Threshold: {confidenceThreshold[0]}%
                  </label>
                  <Slider
                    value={confidenceThreshold}
                    onValueChange={setConfidenceThreshold}
                    max={100}
                    step={1}
                    className="w-full"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Human Override Required</label>
                  <Switch checked={humanOverride} onCheckedChange={setHumanOverride} />
                </div>
              </div>
            </GlassCard>
          </TabsContent>

          {/* System Health */}
          <TabsContent value="health">
            <div className="grid gap-6 md:grid-cols-2">
              <GlassCard className="p-6">
                <h3 className="text-lg font-semibold mb-4">AI System Status</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span>AI Uptime</span>
                      <span>{aiUptime}%</span>
                    </div>
                    <Progress value={aiUptime} className="h-2" />
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span>Alert Processing</span>
                      <span>{alertHealth}%</span>
                    </div>
                    <Progress value={alertHealth} className="h-2" />
                  </div>
                </div>
              </GlassCard>
              <GlassCard className="p-6">
                <h3 className="text-lg font-semibold mb-4">System Indicators</h3>
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-success"></div>
                    <span>Database: Healthy</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-success"></div>
                    <span>API Services: Operational</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-warning"></div>
                    <span>Queue Processing: Degraded</span>
                  </div>
                </div>
              </GlassCard>
            </div>
          </TabsContent>
        </Tabs>

        {/* Confirmation Dialog */}
        <Dialog open={!!action} onOpenChange={() => setAction(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Confirm Action</DialogTitle>
            </DialogHeader>
            <p>
              Are you sure you want to {action} user {selectedUser?.name}?
            </p>
            <DialogFooter>
              <Button variant="outline" onClick={() => setAction(null)}>Cancel</Button>
              <Button onClick={confirmAction}>Confirm</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}