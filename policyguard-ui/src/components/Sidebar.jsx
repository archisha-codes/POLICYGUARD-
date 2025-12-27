import { Menu, ShieldCheck, FileText, AlertTriangle, Settings } from "lucide-react";

export default function Sidebar({ open, setOpen }) {
  return (
    <>
      {/* Hamburger */}
      <button
        onClick={() => setOpen(!open)}
        className="md:hidden fixed top-5 left-5 z-50 bg-white p-2 rounded-xl shadow hover:scale-105 transition"
      >
        <Menu size={22} />
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed md:static top-0 left-0 h-full w-64 
        bg-gradient-to-b from-indigo-700 to-indigo-900 text-white p-6
        transform ${open ? "translate-x-0" : "-translate-x-full"} 
        md:translate-x-0 transition-all duration-300 shadow-2xl z-40`}
      >
        <h2 className="text-2xl font-bold mb-10 tracking-wide">
          PolicyGuard
        </h2>

        <nav className="space-y-5">
          <NavItem icon={<ShieldCheck />} text="Dashboard" />
          <NavItem icon={<FileText />} text="Documents" />
          <NavItem icon={<AlertTriangle />} text="Risk Analysis" />
          <NavItem icon={<Settings />} text="Settings" />
        </nav>
      </aside>
    </>
  );
}

function NavItem({ icon, text }) {
  return (
    <div className="flex items-center gap-3 cursor-pointer px-3 py-2 rounded-lg
      hover:bg-white/10 hover:translate-x-1 transition-all">
      {icon}
      <span>{text}</span>
    </div>
  );
}
