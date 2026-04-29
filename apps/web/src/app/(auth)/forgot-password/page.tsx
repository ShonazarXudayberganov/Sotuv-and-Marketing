import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function ForgotPasswordPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Parolni tiklash</CardTitle>
        <CardDescription>
          Bu sahifa Sprint 3 da to&apos;liq ishlay boshlaydi. Hozircha akkauntni tiklash uchun
          qo&apos;llab-quvvatlash xizmatiga murojaat qiling.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-muted text-sm">📧 support@nexusai.uz</p>
      </CardContent>
    </Card>
  );
}
