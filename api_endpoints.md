## Authentication APIs

1. **POST /api/auth/register**
   - Register new user (farmer or buyer)
   - Request body: `{name, email, password, phone, userType, location}`
   - Response: `{userId, token, userType, userName}`

2. **POST /api/auth/login**
   - Login existing user
   - Request body: `{email, password}`
   - Response: `{userId, token, userType, userName}`

3. **POST /api/auth/logout**
   - Logout user (invalidate token)
   - Headers: `Authorization: Bearer {token}`
   - Response: `{success: true}`

4. **GET /api/auth/verify**
   - Verify token validity
   - Headers: `Authorization: Bearer {token}`
   - Response: `{valid: true, userType, userName}`

## Farmer APIs

5. **GET /api/farmers/stats**
   - Get farmer dashboard statistics
   - Headers: `Authorization: Bearer {token}`
   - Response: `{activeListings, pendingReservations, weeklySales}`

6. **GET /api/farmers/{farmerId}/profile**
   - Get farmer profile details
   - Headers: `Authorization: Bearer {token}`
   - Response: `{name, bio, location, joinDate, rating, products, reviews}`

7. **PUT /api/farmers/{farmerId}/profile**
   - Update farmer profile
   - Headers: `Authorization: Bearer {token}`
   - Request body: `{name, bio, location, contactInfo}`
   - Response: `{success: true}`

## Product APIs

8. **GET /api/products/active**
   - Get all active product listings for a farmer
   - Headers: `Authorization: Bearer {token}`
   - Response: `[{id, name, price, quantity, tags, icon}]`

9. **GET /api/products/{productId}**
   - Get detailed product information
   - Headers: `Authorization: Bearer {token}`
   - Response: `{id, name, description, price, quantity, category, images, farmerId, farmerName}`

10. **POST /api/products**
    - Create new product listing
    - Headers: `Authorization: Bearer {token}`
    - Request body: `{name, description, price, quantity, category, images}`
    - Response: `{id, name, success: true}`

11. **PUT /api/products/{productId}**
    - Update existing product
    - Headers: `Authorization: Bearer {token}`
    - Request body: `{name, description, price, quantity, category, images}`
    - Response: `{success: true}`

12. **DELETE /api/products/{productId}**
    - Delete product listing
    - Headers: `Authorization: Bearer {token}`
    - Response: `{success: true}`

## Reservation APIs

13. **GET /api/reservations/pending**
    - Get pending reservations for farmer
    - Headers: `Authorization: Bearer {token}`
    - Response: `[{id, productName, customerName, pickupTime, quantity}]`

14. **POST /api/reservations/{reservationId}/approve**
    - Approve a reservation
    - Headers: `Authorization: Bearer {token}`
    - Response: `{success: true}`

15. **POST /api/reservations/{reservationId}/reject**
    - Reject a reservation
    - Headers: `Authorization: Bearer {token}`
    - Response: `{success: true}`

16. **POST /api/products/{productId}/reserve**
    - Create a new reservation (buyer)
    - Headers: `Authorization: Bearer {token}`
    - Request body: `{quantity, pickupTime}`
    - Response: `{reservationId, success: true}`

## Sales APIs

17. **GET /api/sales/recent**
    - Get recent sales for farmer
    - Headers: `Authorization: Bearer {token}`
    - Response: `[{id, productName, amount, paymentStatus, receiptPending}]`

18. **POST /api/sales/{saleId}/receipt**
    - Upload payment receipt
    - Headers: `Authorization: Bearer {token}`
    - Request body: `FormData with receipt image`
    - Response: `{success: true, receiptUrl}`

19. **POST /api/sales/{saleId}/complete**
    - Mark sale as completed
    - Headers: `Authorization: Bearer {token}`
    - Response: `{success: true}`

## Urgent Sale APIs

20. **GET /api/urgent-sales**
    - Get all available urgent sales (buyer view)
    - Headers: `Authorization: Bearer {token}`
    - Response: `[{urgent_sale_id, product_name, original_price, reduced_price, quantity, quantity_unit, best_before, reason, image_url, farmer_name}]`

21. **GET /api/farmers/{farmerId}/urgent-sales**
    - Get urgent sales for a specific farmer
    - Headers: `Authorization: Bearer {token}`
    - Response: `[{urgent_sale_id, product_name, original_price, reduced_price, quantity, quantity_unit, best_before, reason, image_url, status}]`

22. **POST /api/urgent-sales**
    - Create new urgent sale listing
    - Headers: `Authorization: Bearer {token}`
    - Request body: `{product_name, original_price, reduced_price, quantity, quantity_unit, best_before, reason}`
    - Response: `{urgent_sale_id, success: true}`

23. **POST /api/urgent-sales/{saleId}/purchase**
    - Purchase an urgent sale item
    - Headers: `Authorization: Bearer {token}`
    - Request body: `{quantity}`
    - Response: `{reservation_id, success: true}`

## Utility APIs

24. **POST /api/upload-image**
    - Upload product or receipt image
    - Headers: `Authorization: Bearer {token}`
    - Request body: `FormData with image file`
    - Response: `{url, success: true}`

25. **GET /api/categories**
    - Get product categories
    - Response: `[{id, name, icon}]`

26. **POST /api/categories/request**
    - Request new product category
    - Headers: `Authorization: Bearer {token}`
    - Request body: `{name, description}`
    - Response: `{success: true, pending: true}`

## Buyer APIs

27. **GET /api/buyers/favorites**
    - Get buyer's favorite products/farmers
    - Headers: `Authorization: Bearer {token}`
    - Response: `[{id, type, name, image}]`

28. **POST /api/buyers/favorites**
    - Add item to favorites
    - Headers: `Authorization: Bearer {token}`
    - Request body: `{id, type}`
    - Response: `{success: true}`

29. **DELETE /api/buyers/favorites/{id}**
    - Remove item from favorites
    - Headers: `Authorization: Bearer {token}`
    - Response: `{success: true}`

30. **GET /api/buyers/orders**
    - Get buyer's order history
    - Headers: `Authorization: Bearer {token}`
    - Response: `[{id, date, products, total, status}]`

## Search and Discovery APIs

31. **GET /api/search**
    - Search products and farmers
    - Query params: `q, category, location, sort`
    - Response: `{products: [...], farmers: [...]}`

32. **GET /api/farmers/nearby**
    - Get farmers near buyer's location
    - Headers: `Authorization: Bearer {token}`
    - Query params: `radius, limit`
    - Response: `[{id, name, location, distance, rating}]`

## Messaging APIs

33. **GET /api/messages/conversations**
    - Get user's conversations
    - Headers: `Authorization: Bearer {token}`
    - Response: `[{id, with, lastMessage, timestamp, unread}]`

34. **GET /api/messages/conversation/{id}**
    - Get messages in a conversation
    - Headers: `Authorization: Bearer {token}`
    - Response: `[{id, sender, content, timestamp, read}]`

35. **POST /api/messages/send**
    - Send a message
    - Headers: `Authorization: Bearer {token}`
    - Request body: `{recipient, content}`
    - Response: `{id, timestamp, success: true}`