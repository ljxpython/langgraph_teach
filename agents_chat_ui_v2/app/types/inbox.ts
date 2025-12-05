import { Thread, ThreadStatus } from "@langchain/langgraph-sdk";

/**
 * 人工中断配置，指定处理中断时允许的操作。
 */
export interface HumanInterruptConfig {
  allow_ignore: boolean;
  allow_respond: boolean;
  allow_edit: boolean;
  allow_accept: boolean;
}
// FIXME  MC80OmFIVnBZMlhtblk3a3ZiUG1yS002UzNOVE53PT06NGJjNzY1YjA=

/**
 * 代理向人工发出的操作请求。
 * 这是 HumanInterrupt 的一部分。
 */
export interface ActionRequest {
  action: string;
  args: Record<string, any>;
}
// NOTE  MS80OmFIVnBZMlhtblk3a3ZiUG1yS002UzNOVE53PT06NGJjNzY1YjA=

/**
 * 表示代理流程中的人工中断。
 * 类似于 LangGraph Interrupt 类型，但具有特定的人工交互字段。
 */
export interface HumanInterrupt {
  action_request: ActionRequest;
  config: HumanInterruptConfig;
  description?: string;
}

/**
 * 人工对代理中断的响应。
 * 匹配 LangGraph SDK 恢复中断的格式。
 */
export type HumanResponse =
  | { type: "approve" }
  | { type: "edit"; edited_action: { name: string; args: Record<string, any> } }
  | { type: "reject"; message: string };

/**
 * 扩展的线程状态类型，包括我们的自定义状态。
 * 基于 LangGraph ThreadStatus 进行扩展。
 */
export type EnhancedThreadStatus = ThreadStatus | "human_response_needed";

/**
 * 基础线程数据接口，包含通用属性。
 * 作为所有线程数据类型的基础。
 */
interface BaseThreadData<T extends Record<string, any> = Record<string, any>> {
  thread: Thread<T>;
  invalidSchema?: boolean;
}

/**
 * 非中断状态的线程数据。
 * 遵循判别联合模式，其中 status 字段作为判别器。
 */
export interface GenericThreadData<
  T extends Record<string, any> = Record<string, any>
> extends BaseThreadData<T> {
  status: "idle" | "busy" | "error" | "human_response_needed";
  interrupts?: undefined;
}
// TODO  Mi80OmFIVnBZMlhtblk3a3ZiUG1yS002UzNOVE53PT06NGJjNzY1YjA=

/**
 * 中断状态的线程数据。
 * 包含特定于中断的附加字段。
 */
export interface InterruptedThreadData<
  T extends Record<string, any> = Record<string, any>
> extends BaseThreadData<T> {
  status: "interrupted";
  interrupts?: HumanInterrupt[];
}

/**
 * 所有线程数据类型的联合类型。
 * 使用判别联合模式以获得更好的类型安全。
 */
export type ThreadData<T extends Record<string, any> = Record<string, any>> =
  | GenericThreadData<T>
  | InterruptedThreadData<T>;

/**
 * 带有特殊"all"选项的线程状态，用于过滤。
 */
export type ThreadStatusWithAll = EnhancedThreadStatus | "all";
// NOTE  My80OmFIVnBZMlhtblk3a3ZiUG1yS002UzNOVE53PT06NGJjNzY1YjA=

/**
 * 代理收件箱配置。
 */
export interface AgentInbox {
  /**
   * 收件箱的唯一标识符。
   */
  id: string;
  /**
   * 图的 ID。
   */
  graphId: string;
  /**
   * 部署的 ID。
   */
  deploymentId: string;
  /**
   * 部署的 URL。可以是 localhost URL 或部署 URL。
   * @deprecated 请改用 deploymentId。
   */
  deploymentUrl?: string;
  /**
   * 收件箱的可选名称，在 UI 中用于标记收件箱。
   */
  name?: string;
  /**
   * 收件箱是否被选中。
   */
  tenantId?: string;
  createdAt: string;
}

