import { lazy, Suspense, useEffect, useState } from "react";
import {
  LayoutDashboard,
  Users,
  Package,
  Truck,
  FileText,
  ShieldCheck,
  ChartColumn,
  Database,
  CalendarDays,
  ChevronRight,
} from "lucide-react";
import "./analysis.css";
import "./evidence.css";

const Overview = lazy(() => import("./pages/Overview"));
const UsersPage = lazy(() => import("./pages/Users"));
const ProductsPage = lazy(() => import("./pages/Products"));
const DeliveryPage = lazy(() => import("./pages/Delivery"));
const FindingsPage = lazy(() => import("./pages/FindingsPage"));
const Quality = lazy(() => import("./pages/Quality"));
const modules = [
  { path: "/", title: "经营总览", icon: LayoutDashboard },
  { path: "/users", title: "用户价值分析", icon: Users },
  { path: "/products", title: "商品与品类", icon: Package },
  { path: "/delivery", title: "履约与评价", icon: Truck },
  { path: "/findings", title: "经营发现", icon: FileText },
  { path: "/quality", title: "数据质量中心", icon: ShieldCheck },
];

export default function App() {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const change = () => setPath(window.location.pathname);
    window.addEventListener("popstate", change);
    return () => window.removeEventListener("popstate", change);
  }, []);
  const navigate = (next: string) => {
    if (next !== path) window.history.pushState({}, "", next);
    setPath(next);
    window.scrollTo(0, 0);
  };
  const title = modules.find((m) => m.path === path)?.title ?? "页面未找到";
  useEffect(() => {
    document.title = `RetailScope · ${title}`;
  }, [title]);
  return (
    <div className="workbench">
      <aside className="sidebar" aria-label="工作台导航">
        <a
          className="brand"
          href="/"
          onClick={(e) => {
            e.preventDefault();
            navigate("/");
          }}
          aria-label="RetailScope 首页"
        >
          <span className="brand-symbol">
            <ChartColumn size={19} />
          </span>
          RetailScope
        </a>
        <p className="brand-description">电商经营分析工作台</p>
        <div className="nav-caption">分析模块</div>
        <nav aria-label="分析模块">
          {modules.map((m) => (
            <a
              key={m.path}
              href={m.path}
              className={`nav-link ${path === m.path ? "active" : ""}`}
              aria-current={path === m.path ? "page" : undefined}
              onClick={(e) => {
                if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
                e.preventDefault();
                navigate(m.path);
              }}
            >
              <m.icon size={18} />
              {m.title}
            </a>
          ))}
        </nav>
        <details className="sidebar-bottom about-data"><summary><Database size={15} />关于数据</summary>
          <div className="data-source">
            <Database size={15} />
            <strong><a href="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce" target="_blank" rel="noreferrer">Olist / Kaggle</a></strong>
          </div>
          <p>
            2016–2018 历史样本
            <br />
            CC BY-NC-SA 4.0
            <br />非商业个人作品
          </p>
        </details>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            分析工作台
            <ChevronRight size={13} />
            <span>{title}</span>
          </div>
          <span className="historic-label">
            <CalendarDays size={13} />
            历史数据分析
          </span>
        </header>
        <Suspense
          fallback={
            <main>
              <div className="skeleton-chart" role="status">
                正在加载分析页面…
              </div>
            </main>
          }
        >
          {path === "/" ? (
            <Overview onOpenFindings={() => navigate("/findings")} />
          ) : path === "/users" ? (
            <UsersPage />
          ) : path === "/products" ? (
            <ProductsPage />
          ) : path === "/delivery" ? (
            <DeliveryPage />
          ) : path === "/findings" ? (
            <FindingsPage />
          ) : path === "/quality" ? (
            <Quality />
          ) : (
            <main>
              <section className="state-panel">
                <h1>页面未找到</h1>
                <a
                  href="/"
                  onClick={(e) => {
                    e.preventDefault();
                    navigate("/");
                  }}
                >
                  返回经营总览
                </a>
              </section>
            </main>
          )}
        </Suspense>
      </div>
    </div>
  );
}
