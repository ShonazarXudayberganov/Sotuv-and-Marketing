import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Page() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Tarif va to&apos;lovlar</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted text-sm">
          Bu sahifa Sprint 4-5 da to&apos;liq ishga tushadi.
        </p>
      </CardContent>
    </Card>
  );
}
