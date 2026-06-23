"use client";

import { motion, Variants } from "framer-motion";
import Link from "next/link";
import { ArrowRight, ShieldAlert, Zap, Layers, Video } from "lucide-react";

export default function LandingPage() {
  const fadeUp: Variants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
  };

  const stagger: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.2 } },
  };

  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans selection:bg-blue-100">
      {/* Hero Section */}
      <section className="relative h-screen w-full flex flex-col items-center justify-center overflow-hidden">
        {/* Video Background */}
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover z-0"
        >
          <source src="/landing.mp4" type="video/mp4" />
        </video>
        
        {/* Dark Overlay for Text Readability */}
        <div className="absolute inset-0 bg-black/60 z-10" />

        {/* Hero Content */}
        <div className="relative z-20 text-center px-6 max-w-4xl mx-auto flex flex-col items-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <span className="inline-block py-1 px-3 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-sm font-medium tracking-wide mb-6 backdrop-blur-md">
              Flipkart Gridlock 2.0
            </span>
            <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight mb-6 leading-tight">
              Bring Order to <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
                Urban Chaos
              </span>
            </h1>
            <p className="text-lg md:text-xl text-slate-300 mb-10 max-w-2xl mx-auto font-light leading-relaxed">
              Production-grade, AI-powered traffic violation detection built specifically for the unpredictable nature of Indian roads.
            </p>
            <Link href="/dashboard">
              <button className="group relative inline-flex items-center justify-center px-8 py-4 font-bold text-white transition-all duration-200 bg-blue-600 border border-transparent rounded-full hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-600 hover:scale-105 shadow-[0_0_40px_-10px_rgba(37,99,235,0.5)]">
                Launch Dashboard
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
            </Link>
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <motion.div 
          className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center text-white/50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 1 }}
        >
          <span className="text-xs uppercase tracking-widest mb-2 font-semibold">Scroll to Discover</span>
          <div className="w-[1px] h-12 bg-gradient-to-b from-white/50 to-transparent" />
        </motion.div>
      </section>

      {/* Why is it required? */}
      <section className="py-24 px-6 max-w-6xl mx-auto">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="text-center max-w-3xl mx-auto mb-20"
        >
          <h2 className="text-4xl font-bold mb-6 text-slate-900 tracking-tight">Why Gridlock 2.0?</h2>
          <div className="w-16 h-1 bg-blue-500 mx-auto mb-8 rounded-full" />
          <p className="text-xl text-slate-600 leading-relaxed">
            Traffic management in India is incredibly complex. Standard AI solutions fail because our roads are unpredictable, vehicle types are wildly diverse (from auto-rickshaws to heavy trucks), and license plates don't always follow standard formats.
            <br /><br />
            Manual enforcement simply cannot scale. We need a system that understands the chaos and automates the enforcement pipeline without human bottlenecks.
          </p>
        </motion.div>
      </section>

      {/* What we are solving */}
      <section className="py-24 px-6 bg-slate-50 border-y border-slate-100">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={fadeUp}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-6 text-slate-900 tracking-tight">What We Are Solving</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              We developed a robust 7-stage machine learning pipeline that automatically processes CCTV feeds and identifies 8 different violation types in real-time.
            </p>
          </motion.div>

          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-50px" }}
            variants={stagger}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8"
          >
            {[
              { icon: <ShieldAlert className="w-8 h-8 text-blue-500" />, title: "8 Violation Types", desc: "Detects Helmets, Seatbelts, Wrong-side, Triple Riding, No Plate, and more." },
              { icon: <Zap className="w-8 h-8 text-amber-500" />, title: "Real-Time Inference", desc: "Runs multiple YOLO11 models in parallel at 30+ FPS on edge GPU hardware." },
              { icon: <Layers className="w-8 h-8 text-emerald-500" />, title: "Tamper-Proof Evidence", desc: "Generates cryptographic hashes, annotated images, and 3s video clips for every offense." },
              { icon: <Video className="w-8 h-8 text-purple-500" />, title: "Adaptive Enhancement", desc: "Automatically clears hazy, rainy, or low-light scenes before detection." },
            ].map((feature, i) => (
              <motion.div key={i} variants={fadeUp} className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
                <div className="bg-slate-50 w-16 h-16 rounded-xl flex items-center justify-center mb-6">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold mb-3 text-slate-900">{feature.title}</h3>
                <p className="text-slate-600 leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-24 px-6 max-w-6xl mx-auto">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUp}
          className="text-center mb-16"
        >
          <h2 className="text-4xl font-bold mb-6 text-slate-900 tracking-tight">The Team</h2>
          <div className="w-16 h-1 bg-blue-500 mx-auto mb-12 rounded-full" />
          
          <div className="flex flex-wrap justify-center gap-6 md:gap-12">
            {[
              "Vaidik Saxena",
              "Nishchal Chandel",
              "Vinayak Goel",
              "Smarak Gartia"
            ].map((name) => (
              <motion.div 
                key={name}
                whileHover={{ y: -5 }}
                className="flex flex-col items-center"
              >
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-100 to-blue-50 border-4 border-white shadow-lg flex items-center justify-center mb-4">
                  <span className="text-2xl font-bold text-blue-600">
                    {name.split(" ").map(n => n[0]).join("")}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-800">{name}</h3>
                <p className="text-sm text-slate-500">Gridlock 2.0</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-slate-500 border-t border-slate-100 text-sm">
        <p>© {new Date().getFullYear()} Gridlock 2.0. Built for Flipkart Gridlock Hackathon.</p>
      </footer>
    </div>
  );
}
