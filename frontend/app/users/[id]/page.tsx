import UserDetailPage from "@/modules/user/pages/UserDetailPage";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function Page({ params }: PageProps) {
  const { id } = await params;
  const userId = Number(id);
  return <UserDetailPage userId={userId} />;
}
