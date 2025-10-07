import { Card, CardContent } from "@/components/ui/card";
import { IndianRupee, Clock, Leaf, Heart } from "lucide-react";

const benefits = [
  {
    icon: IndianRupee,
    title: "₹5,000+ Saved Monthly",
    description: "Smart shopping, bulk buying, and waste reduction translate to real savings",
    stat: "30% Cost Reduction",
    color: "text-primary",
    gradient: "from-primary/20 to-primary/5",
  },
  {
    icon: Leaf,
    title: "40% Less Food Waste",
    description: "Smart consumption tracking and recipe suggestions mean fresh food gets used",
    stat: "Eco-Friendly Living",
    color: "text-accent",
    gradient: "from-accent/20 to-accent/5",
  },
  {
    icon: Heart,
    title: "Peace of Mind",
    description: "Medicine tracking, emergency prep, and festival planning - all handled",
    stat: "Stress-Free Home",
    color: "text-primary",
    gradient: "from-primary/20 to-primary/5",
  },
];

export const Benefits = () => {
  return (
    <section className="py-24 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-4 animate-fade-in">
          <h2 className="text-4xl lg:text-5xl font-bold text-foreground">
            Real Impact,
            <span className="text-primary"> Measured Results</span>
          </h2>
          <p className="text-xl text-muted-foreground">
            Join thousands of Indian families already transforming their households
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
          {benefits.map((benefit, index) => (
            <Card 
              key={index}
              className="group hover:shadow-medium transition-smooth border-border/50 animate-scale-in overflow-hidden"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className={`h-2 bg-gradient-to-r ${benefit.gradient}`} />
              <CardContent className="p-6 space-y-4">
                <div className="w-14 h-14 rounded-2xl gradient-feature flex items-center justify-center group-hover:scale-110 transition-smooth">
                  <benefit.icon className={`w-7 h-7 ${benefit.color}`} />
                </div>
                
                <div className="space-y-2">
                  <div className={`text-sm font-semibold ${benefit.color}`}>
                    {benefit.stat}
                  </div>
                  <h3 className="text-xl font-bold">{benefit.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {benefit.description}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};
