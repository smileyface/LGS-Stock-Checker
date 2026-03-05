/**
 * These types align with backend/schema/messaging/messages.py
 */

// 1. Define the possible message types (Event names)
export type MessageType = 
  | 'task_update' 
  | 'card_update' 
  | 'notification' 
  | 'system';

/************BLOCKS***************/
export type CardSchema = 
    { name: string }

export type FinishSchema = "non-foil"| "foil"| "etched"

export type SetSchema = 
    | { code: string; name: string }
    | { code: string; name?: never }
    | { code?: never; name: string };

export type UserSchema = 
    { username: string }

export interface CardSpecificationSchema{
    set_code?: SetSchema
    collector_number?: string
    finish?: FinishSchema
}

export interface CardPreferenceSchema{
    card: CardSchema
    amount?: number
    card_specs?: CardSpecificationSchema[]
}

/*************PAYLOADS*************/
export interface UpdateCardRequestPayload{
    command: "add" | "delete" | "update"
    update_data: CardPreferenceSchema
}

export interface LoginUserPayload{
    user: UserSchema
    password: string
}

/***********SEND_MESSAGES*************/
export interface UpdateCardRequest{
    name: string
    payload: UpdateCardRequestPayload
}

export interface LoginUserMessage{
    name: "login_user_me"
    payload: LoginUserPayload
}

export interface GetCardsMessage{
    name: "get_cards"
    payload: {}
}

export type AppMessage = 
    | UpdateCardRequest
    | LoginUserMessage
    | GetCardsMessage