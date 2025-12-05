// NOTE  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002ZGpZMFRBPT06MjYzZTg2NWU=

"use client";
// FIXME  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002ZGpZMFRBPT06MjYzZTg2NWU=

import React, { useState, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { CheckCircle, XCircle, Edit3, ChevronDown, ChevronUp } from "lucide-react";
import { Interrupt } from "@langchain/langgraph-sdk";
import { HumanInterrupt, HumanResponse } from "@/app/types/inbox";
import { cn } from "@/lib/utils";

interface InterruptActionsProps {
  interrupt: Interrupt;
  onSubmit: (responses: HumanResponse[]) => void;
  isLoading?: boolean;
}
// NOTE  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002ZGpZMFRBPT06MjYzZTg2NWU=

type DecisionMode = "idle" | "edit" | "reject";
// NOTE  My80OmFIVnBZMlhtblk3a3ZiUG1yS002ZGpZMFRBPT06MjYzZTg2NWU=

interface InterruptDecision {
  mode: DecisionMode;
  editedArgs?: Record<string, any>;
  rejectMessage?: string;
}

/**
 * InterruptActions 组件
 *
 * 用于渲染需要人工批准的 LangGraph 中断的默认组件。
 * 此组件支持深度代理的标准中断工作流程：
 * - 批准：按原样执行工具调用
 * - 编辑：在执行前修改工具参数
 * - 拒绝：取消工具调用并提供反馈
 *
 * 该组件自动处理单个中断中的多个工具调用，
 * 并遵循中断配置中配置的权限。
 */
export const InterruptActions = React.memo<InterruptActionsProps>(
  ({ interrupt, onSubmit, isLoading = false }) => {
    // 从中断值解析中断
    const interrupts = useMemo(() => {
      try {
        const value = interrupt.value as any;

        if (!value) {
          return [];
        }

        // 处理 Deep Agents/LangGraph 格式: { action_requests: [], review_configs: [] }
        if (
          typeof value === "object" &&
          !Array.isArray(value) &&
          Array.isArray(value.action_requests) &&
          Array.isArray(value.review_configs)
        ) {
          const parsed = value.action_requests.map((actionReq: any, idx: number) => {
            const reviewConfig = value.review_configs[idx] || {};
            const allowedDecisions = reviewConfig.allowed_decisions || [];

            return {
              action_request: {
                action: actionReq.name || actionReq.action || "未知操作",
                args: actionReq.args || actionReq.arguments || {},
              },
              config: {
                allow_accept: allowedDecisions.includes("approve"),
                allow_edit: allowedDecisions.includes("edit"),
                allow_respond: allowedDecisions.includes("reject"),
                allow_ignore: allowedDecisions.includes("ignore"),
              },
              description: actionReq.description,
            };
          }) as HumanInterrupt[];
          return parsed;
        }

        // 如果是标准格式中断数组
        if (Array.isArray(value)) {
          const filtered = value.filter(
            (item) =>
              item &&
              typeof item === "object" &&
              item.action_request &&
              typeof item.action_request === "object"
          ) as HumanInterrupt[];
          return filtered;
        }

        // 如果是标准格式的单个对象
        if (
          typeof value === "object" &&
          value.action_request &&
          typeof value.action_request === "object"
        ) {
          return [value] as HumanInterrupt[];
        }

        return [];
      } catch (error) {
        console.error("解析中断时出错:", error);
        return [];
      }
    }, [interrupt]);

    // 管理每个中断决策的状态
    const [decisions, setDecisions] = useState<Record<number, InterruptDecision>>(
      {}
    );

    // 默认折叠所有参数以保持 UI 整洁
    const [expandedArgs, setExpandedArgs] = useState<
      Record<number, Record<string, boolean>>
    >({});

    // 切换特定中断和参数键的参数展开
    const toggleArgExpanded = useCallback((interruptIdx: number, argKey: string) => {
      setExpandedArgs((prev) => ({
        ...prev,
        [interruptIdx]: {
          ...(prev[interruptIdx] || {}),
          [argKey]: !prev[interruptIdx]?.[argKey],
        },
      }));
    }, []);

    // 为特定中断设置决策模式
    const setDecisionMode = useCallback(
      (idx: number, mode: DecisionMode, initialArgs?: Record<string, any>) => {
        setDecisions((prev) => ({
          ...prev,
          [idx]: {
            mode,
            editedArgs: mode === "edit" ? initialArgs : undefined,
            rejectMessage: mode === "reject" ? "" : undefined,
          },
        }));
      },
      []
    );

    // 更新特定中断的拒绝消息
    const updateRejectMessage = useCallback((idx: number, message: string) => {
      setDecisions((prev) => ({
        ...prev,
        [idx]: {
          ...(prev[idx] || { mode: "reject" as DecisionMode }),
          rejectMessage: message,
        },
      }));
    }, []);

    // 更新特定中断的编辑参数
    const updateEditedArgs = useCallback(
      (idx: number, key: string, value: string) => {
        setDecisions((prev) => {
          const current = prev[idx] || { mode: "edit" as DecisionMode };
          const currentArgs = current.editedArgs || {};

          // 如果看起来像 JSON 则尝试解析，否则作为字符串使用
          let parsedValue: any = value;
          try {
            if (value.trim().startsWith("{") || value.trim().startsWith("[")) {
              parsedValue = JSON.parse(value);
            }
          } catch {
            // 如果不是有效 JSON 则保持为字符串
            parsedValue = value;
          }

          return {
            ...prev,
            [idx]: {
              ...current,
              editedArgs: {
                ...currentArgs,
                [key]: parsedValue,
              },
            },
          };
        });
      },
      []
    );

    // 处理所有决策的提交
    const handleSubmit = useCallback(() => {
      const responses: HumanResponse[] = interrupts.map((interrupt, idx) => {
        // 跳过无效中断
        if (!interrupt?.action_request) {
          return { type: "approve" as const };
        }

        const decision = decisions[idx];

        if (!decision || decision.mode === "idle") {
          // 如果没有做决策则默认批准
          return { type: "approve" as const };
        }

        if (decision.mode === "edit") {
          return {
            type: "edit" as const,
            edited_action: {
              name: interrupt.action_request.action || "unknown",
              args: decision.editedArgs || interrupt.action_request.args || {},
            },
          };
        }

        if (decision.mode === "reject") {
          const userMessage = decision.rejectMessage?.trim() || "";
          // 在消息前添加"用户拒绝："前缀
          const fullMessage = userMessage
            ? `用户拒绝：${userMessage}`
            : "用户拒绝";
          return {
            type: "reject" as const,
            message: fullMessage,
          };
        }

        return { type: "approve" as const };
      });

      onSubmit(responses);
    }, [interrupts, decisions, onSubmit]);

    if (interrupts.length === 0) {
      return null;
    }

    return (
      <div className="w-full space-y-4 rounded-lg border-2 border-orange-300 bg-orange-50/80 p-4 dark:border-orange-700 dark:bg-orange-950/30">
        {interrupts.map((humanInterrupt, idx) => {
          // 中断结构的防御性检查
          if (!humanInterrupt || !humanInterrupt.action_request) {
            return null;
          }

          const { action_request, config, description } = humanInterrupt;
          const decision = decisions[idx];
          const isEditing = decision?.mode === "edit";
          const isRejecting = decision?.mode === "reject";

          // 如果缺少配置则提供默认值
          const safeConfig = config || {
            allow_accept: true,
            allow_edit: true,
            allow_respond: true,
            allow_ignore: false,
          };

          // 为 action_request 提供默认值
          const safeActionRequest = {
            action: action_request.action || "未知操作",
            args: action_request.args || {},
          };

          return (
            <div
              key={idx}
              className={cn(
                "rounded-lg border-2 bg-card p-4 shadow-sm transition-colors",
                isEditing && "border-blue-500 bg-blue-50/50 dark:bg-blue-950/20",
                isRejecting && "border-red-500 bg-red-50/50 dark:bg-red-950/20",
                !isEditing &&
                  !isRejecting &&
                  "border-orange-500 bg-orange-50/50 dark:bg-orange-950/20"
              )}
            >
              {/* 头部 */}
              <div className="mb-4 flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="rounded-md bg-orange-100 px-2 py-1 text-xs font-semibold text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                      需要批准
                    </span>
                    {interrupts.length > 1 && (
                      <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                        第 {idx + 1} 个，共 {interrupts.length} 个
                      </span>
                    )}
                  </div>
                  <h3 className="mt-3 text-xl font-bold text-gray-900 dark:text-gray-100">
                    {safeActionRequest.action}
                  </h3>
                  <p className="mt-1 text-sm font-medium text-gray-700 dark:text-gray-200">
                    请查看以下工具参数并选择操作
                  </p>
                </div>
              </div>

              {/* 工具参数 */}
              <div className="mb-4 space-y-2">
                <h4 className="mb-1 text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-300">
                  参数
                </h4>
                {isEditing ? (
                  <div className="space-y-2">
                    {Object.entries(safeActionRequest.args).map(([key, value]) => (
                      <div key={key} className="rounded-sm border border-border">
                        <div className="bg-muted/30 p-2">
                          <label className="font-mono text-xs font-semibold text-gray-900 dark:text-gray-100">
                            {key}
                          </label>
                        </div>
                        <div className="p-2">
                          <Textarea
                            value={
                              decision.editedArgs?.[key] !== undefined
                                ? typeof decision.editedArgs[key] === "string"
                                  ? decision.editedArgs[key]
                                  : JSON.stringify(decision.editedArgs[key], null, 2)
                                : typeof value === "string"
                                  ? value
                                  : JSON.stringify(value, null, 2)
                            }
                            onChange={(e) =>
                              updateEditedArgs(idx, key, e.target.value)
                            }
                            className="min-h-[60px] font-mono text-xs"
                            placeholder={`输入 ${key}...`}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {Object.entries(safeActionRequest.args).map(([key, value]) => {
                      const isExpanded = expandedArgs[idx]?.[key];
                      const stringValue =
                        typeof value === "string"
                          ? value
                          : JSON.stringify(value, null, 2);
                      const isLong = stringValue.length > 200;
                      const preview = isLong
                        ? stringValue.slice(0, 100) + "..."
                        : stringValue;

                      return (
                        <div
                          key={key}
                          className="rounded-md border border-border bg-card"
                        >
                          <button
                            onClick={() => toggleArgExpanded(idx, key)}
                            className="flex w-full items-center justify-between bg-muted p-3 text-left transition-colors hover:bg-muted/80"
                          >
                            <span className="font-mono text-sm font-semibold">
                              {key}
                            </span>
                            {isExpanded ? (
                              <ChevronUp size={16} />
                            ) : (
                              <ChevronDown size={16} />
                            )}
                          </button>
                          {isExpanded ? (
                            <div className="border-t border-border p-3">
                              <pre className="m-0 max-h-96 overflow-auto whitespace-pre-wrap break-words font-mono text-xs">
                                {stringValue}
                              </pre>
                            </div>
                          ) : (
                            <div className="border-t border-border p-3">
                              <p className="m-0 truncate font-mono text-sm">
                                {preview}
                              </p>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* 拒绝消息输入 */}
              {isRejecting && (
                <div className="mb-4">
                  <label className="mb-2 block text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-300">
                    反馈给代理（可选）
                  </label>
                  <Textarea
                    value={decision.rejectMessage || ""}
                    onChange={(e) => updateRejectMessage(idx, e.target.value)}
                    placeholder="解释为什么不应执行此操作以及代理应该怎么做..."
                    className="min-h-[80px]"
                  />
                  <p className="mt-1 text-xs font-medium text-gray-600 dark:text-gray-300">
                    此反馈将添加到对话中以帮助引导代理。
                  </p>
                </div>
              )}

              {/* 操作按钮 */}
              <div className="flex flex-wrap gap-2">
                {safeConfig.allow_accept && !isEditing && !isRejecting && (
                  <Button
                    onClick={
                      interrupts.length === 1
                        ? handleSubmit
                        : () => setDecisionMode(idx, "idle")
                    }
                    variant="default"
                    size="sm"
                    className="bg-green-600 text-white hover:bg-green-700"
                    disabled={isLoading}
                  >
                    <CheckCircle size={14} />
                    <span className="font-semibold">批准</span>
                  </Button>
                )}

                {safeConfig.allow_edit && !isRejecting && (
                  <Button
                    onClick={() => {
                      if (isEditing) {
                        // 提交编辑版本
                        if (interrupts.length === 1) {
                          handleSubmit();
                        } else {
                          // 对于多个中断，只标记为准备提交
                          setDecisionMode(idx, "idle");
                        }
                      } else {
                        // 进入编辑模式
                        setDecisionMode(idx, "edit", safeActionRequest.args);
                      }
                    }}
                    variant={isEditing ? "default" : "outline"}
                    size="sm"
                    disabled={isLoading}
                    className={
                      isEditing ? "bg-blue-600 text-white hover:bg-blue-700" : ""
                    }
                  >
                    <Edit3 size={14} />
                    <span className="font-semibold">
                      {isEditing
                        ? interrupts.length === 1
                          ? "提交编辑"
                          : "完成编辑"
                        : "编辑"}
                    </span>
                  </Button>
                )}

                {safeConfig.allow_respond && !isEditing && (
                  <Button
                    onClick={() => {
                      if (isRejecting) {
                        // 提交拒绝
                        if (interrupts.length === 1) {
                          handleSubmit();
                        } else {
                          // 对于多个中断，只标记为准备提交
                          setDecisionMode(idx, "idle");
                        }
                      } else {
                        // 进入拒绝模式
                        setDecisionMode(idx, "reject");
                      }
                    }}
                    variant={isRejecting ? "default" : "outline"}
                    size="sm"
                    className={
                      isRejecting
                        ? "bg-red-600 text-white hover:bg-red-700"
                        : "border-red-500 text-red-600 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950"
                    }
                    disabled={isLoading}
                  >
                    <XCircle size={14} />
                    <span className="font-semibold">
                      {isRejecting
                        ? interrupts.length === 1
                          ? "提交拒绝"
                          : "确认拒绝"
                        : "拒绝"}
                    </span>
                  </Button>
                )}

                {(isEditing || isRejecting) && (
                  <Button
                    onClick={() => setDecisionMode(idx, "idle")}
                    variant="ghost"
                    size="sm"
                    disabled={isLoading}
                    className="text-gray-700 hover:text-gray-900 dark:text-gray-200 dark:hover:text-white"
                  >
                    <span className="font-semibold">取消</span>
                  </Button>
                )}
              </div>
            </div>
          );
        })}

        {/* 提交全部按钮（用于多个中断） */}
        {interrupts.length > 1 && (
          <div className="flex justify-end pt-2">
            <Button
              onClick={handleSubmit}
              disabled={isLoading}
              size="lg"
              className="bg-blue-600 font-semibold text-white hover:bg-blue-700"
            >
              {isLoading ? (
                "提交中..."
              ) : (
                <>提交全部决策 ({interrupts.length})</>
              )}
            </Button>
          </div>
        )}
      </div>
    );
  }
);

InterruptActions.displayName = "InterruptActions";

