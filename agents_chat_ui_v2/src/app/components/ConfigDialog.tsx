// TODO  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002Y1RGNVZBPT06NDM3ZTAxMjk=

"use client";
// NOTE  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002Y1RGNVZBPT06NDM3ZTAxMjk=

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { StandaloneConfig } from "@/lib/config";
// FIXME  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002Y1RGNVZBPT06NDM3ZTAxMjk=

interface ConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (config: StandaloneConfig) => void;
  initialConfig?: StandaloneConfig;
}
// NOTE  My80OmFIVnBZMlhtblk3a3ZiUG1yS002Y1RGNVZBPT06NDM3ZTAxMjk=

export function ConfigDialog({
  open,
  onOpenChange,
  onSave,
  initialConfig,
}: ConfigDialogProps) {
  const [deploymentUrl, setDeploymentUrl] = useState(
    initialConfig?.deploymentUrl || ""
  );
  const [assistantId, setAssistantId] = useState(
    initialConfig?.assistantId || ""
  );
  const [langsmithApiKey, setLangsmithApiKey] = useState(
    initialConfig?.langsmithApiKey || ""
  );

  useEffect(() => {
    if (open && initialConfig) {
      setDeploymentUrl(initialConfig.deploymentUrl);
      setAssistantId(initialConfig.assistantId);
      setLangsmithApiKey(initialConfig.langsmithApiKey || "");
    }
  }, [open, initialConfig]);

  const handleSave = () => {
    if (!deploymentUrl || !assistantId) {
      alert("请填写所有必填字段");
      return;
    }

    onSave({
      deploymentUrl,
      assistantId,
      langsmithApiKey: langsmithApiKey || undefined,
    });
    onOpenChange(false);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>配置</DialogTitle>
          <DialogDescription>
            配置您的 智能体 部署设置。这些设置将保存在浏览器的本地存储中。
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="deploymentUrl">部署 URL</Label>
            <Input
              id="deploymentUrl"
              placeholder="https://<部署地址>"
              value={deploymentUrl}
              onChange={(e) => setDeploymentUrl(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="assistantId">助手 ID</Label>
            <Input
              id="assistantId"
              placeholder="<助手ID>"
              value={assistantId}
              onChange={(e) => setAssistantId(e.target.value)}
            />
          </div>
          {/*<div className="grid gap-2">*/}
          {/*  <Label htmlFor="langsmithApiKey">*/}
          {/*    LangSmith API 密钥{" "}*/}
          {/*    <span className="text-muted-foreground">(可选)</span>*/}
          {/*  </Label>*/}
          {/*  <Input*/}
          {/*    id="langsmithApiKey"*/}
          {/*    type="password"*/}
          {/*    placeholder="lsv2_pt_..."*/}
          {/*    value={langsmithApiKey}*/}
          {/*    onChange={(e) => setLangsmithApiKey(e.target.value)}*/}
          {/*  />*/}
          {/*</div>*/}
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            取消
          </Button>
          <Button onClick={handleSave}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
