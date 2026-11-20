---
name: typescript-patterns
description: "TypeScript 5+ types, interfaces, unknown narrowing, strict immutability, and API patterns. Defer to angular-developer for Angular."
---

# TypeScript & JavaScript Design Patterns

Idiomatic TypeScript patterns, interface contracts, and type-narrowing standards for robust applications.

## When to Activate

- Writing or refactoring TypeScript / JavaScript modules
- Defining public APIs, DTOs, interfaces, and shared type definitions
- Narrowing `unknown` or external API responses safely without `any`
- Designing custom hooks, utility types, and repository interfaces
- Do NOT use for Angular-specific code (activate `angular-developer` instead)

## Core Principles

### 1. Explicit Public APIs & Type Inference

Add explicit parameter and return types to exported functions, classes, and shared utilities. Let the compiler infer obvious local variable types.

```typescript
// Good: Explicit types on public contract
export interface UserProfile {
  id: string
  email: string
  role: 'admin' | 'member'
}

export function formatUserProfile(user: UserProfile): string {
  return `${user.email} (${user.role})`
}
```

### 2. Interfaces vs Type Aliases

- Use `interface` for object shapes, models, and contracts that can be extended or implemented.
- Use `type` for unions, intersections, tuples, mapped types, and utility types.
- Prefer string literal unions over numerical `enum`.

```typescript
export interface Identifiable {
  id: string
}

export type EntityStatus = 'pending' | 'active' | 'archived'
export type WithStatus<T> = T & { status: EntityStatus }
```

### 3. Absolute Prohibition of `any`

Never use `any` in application code. Use `unknown` for external, untrusted, or serialized input, and narrow it safely using native type guards or `instanceof`.

```typescript
// Good: Safe type narrowing with unknown
export function extractErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  return 'Unknown error occurred'
}
```

### 4. Repository & Standard API Response Patterns

Standardize client and service response shapes with generic containers:

```typescript
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: {
    total: number
    page: number
    limit: number
  }
}

export interface CrudRepository<T, ID = string> {
  findById(id: ID): Promise<T | null>
  findAll(): Promise<T[]>
  create(data: Omit<T, 'id'>): Promise<T>
  update(id: ID, data: Partial<T>): Promise<T>
  delete(id: ID): Promise<void>
}
```

### 5. Secret & Configuration Safety

Never hardcode credentials or tokens in TypeScript code. Validate presence at application initialization:

```typescript
export function getRequiredEnv(name: string): string {
  const value = process.env[name]
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`)
  }
  return value
}
```
