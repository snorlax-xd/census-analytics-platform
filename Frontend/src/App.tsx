import { Navigate, Route, Routes } from "react-router-dom";

import { Nav } from "./components/Nav";
import { StateDetail } from "./pages/StateDetail";
import { Tab1 } from "./pages/Tab1";
import { Tab2 } from "./pages/Tab2";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <Nav />
      <Routes>
        <Route path="/" element={<Navigate to="/tab1" replace />} />
        <Route path="/tab1" element={<Tab1 />} />
        <Route path="/tab1/state/:id" element={<StateDetail />} />
        <Route path="/tab2" element={<Tab2 />} />
      </Routes>
    </div>
  );
}
