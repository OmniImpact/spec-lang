/* Runtime Vulkan backend for Linux (Wayland WSI via dlopen("libvulkan.so.1")).
 * Zero compile-time dependency on <vulkan/vulkan.h>.
 * Non-Linux platforms receive clean no-op stubs.
 */

#if defined(__linux__)

#define SPEC_VK_NO_PROTOTYPES

/* Basic Vulkan scalar and handle types */
typedef int32_t SpecVkResult;
typedef uint32_t SpecVkBool32;
typedef uint32_t SpecVkFlags;
typedef uint64_t SpecVkDeviceSize;
typedef uint64_t SpecVkHandle64;

typedef void* SpecVkInstance;
typedef void* SpecVkPhysicalDevice;
typedef void* SpecVkDevice;
typedef void* SpecVkQueue;
typedef void* SpecVkCommandBuffer;

typedef SpecVkHandle64 SpecVkSurfaceKHR;
typedef SpecVkHandle64 SpecVkSwapchainKHR;
typedef SpecVkHandle64 SpecVkImage;
typedef SpecVkHandle64 SpecVkImageView;
typedef SpecVkHandle64 SpecVkRenderPass;
typedef SpecVkHandle64 SpecVkFramebuffer;
typedef SpecVkHandle64 SpecVkShaderModule;
typedef SpecVkHandle64 SpecVkPipelineLayout;
typedef SpecVkHandle64 SpecVkPipeline;
typedef SpecVkHandle64 SpecVkCommandPool;
typedef SpecVkHandle64 SpecVkSemaphore;
typedef SpecVkHandle64 SpecVkFence;
typedef SpecVkHandle64 SpecVkBuffer;
typedef SpecVkHandle64 SpecVkDeviceMemory;
typedef SpecVkHandle64 SpecVkPipelineCache;
typedef SpecVkHandle64 SpecVkSampler;
typedef SpecVkHandle64 SpecVkDescriptorSetLayout;
typedef SpecVkHandle64 SpecVkDescriptorPool;
typedef SpecVkHandle64 SpecVkDescriptorSet;

#define SPEC_VK_NULL_HANDLE 0ULL
#define SPEC_VK_SUCCESS 0
#define SPEC_VK_SUBOPTIMAL_KHR 1000001003
#define SPEC_VK_ERROR_OUT_OF_DATE_KHR (-1000001004)
#define SPEC_VK_TRUE 1U
#define SPEC_VK_FALSE 0U
#define SPEC_VK_MAKE_API_VERSION(variant, major, minor, patch) \
    ((((uint32_t)(variant)) << 29) | (((uint32_t)(major)) << 22) | (((uint32_t)(minor)) << 12) | ((uint32_t)(patch)))

/* Structure type constants */
#define SPEC_VK_STRUCTURE_TYPE_APPLICATION_INFO 0
#define SPEC_VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO 1
#define SPEC_VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO 2
#define SPEC_VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO 3
#define SPEC_VK_STRUCTURE_TYPE_SUBMIT_INFO 4
#define SPEC_VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO 5
#define SPEC_VK_STRUCTURE_TYPE_FENCE_CREATE_INFO 8
#define SPEC_VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO 9
#define SPEC_VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO 12
#define SPEC_VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO 14
#define SPEC_VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO 15
#define SPEC_VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO 16
#define SPEC_VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO 18
#define SPEC_VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO 19
#define SPEC_VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO 20
#define SPEC_VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO 22
#define SPEC_VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO 23
#define SPEC_VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO 24
#define SPEC_VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO 25
#define SPEC_VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO 26
#define SPEC_VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO 27
#define SPEC_VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO 28
#define SPEC_VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO 30
#define SPEC_VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO 31
#define SPEC_VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO 32
#define SPEC_VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO 33
#define SPEC_VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO 34
#define SPEC_VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET 35
#define SPEC_VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO 37
#define SPEC_VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO 38
#define SPEC_VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO 39
#define SPEC_VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO 40
#define SPEC_VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO 42
#define SPEC_VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO 43
#define SPEC_VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER 45
#define SPEC_VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR 1000001000
#define SPEC_VK_STRUCTURE_TYPE_PRESENT_INFO_KHR 1000001001
#define SPEC_VK_STRUCTURE_TYPE_WAYLAND_SURFACE_CREATE_INFO_KHR 1000006000

/* Enums / bitmasks */
#define SPEC_VK_QUEUE_GRAPHICS_BIT 0x00000001U
#define SPEC_VK_FORMAT_B8G8R8A8_SRGB 50U
#define SPEC_VK_FORMAT_B8G8R8A8_UNORM 44U
#define SPEC_VK_FORMAT_R32G32_SFLOAT 103U
#define SPEC_VK_FORMAT_R32G32B32_SFLOAT 106U
#define SPEC_VK_FORMAT_D32_SFLOAT 126U
#define SPEC_VK_COLOR_SPACE_SRGB_NONLINEAR_KHR 0U
#define SPEC_VK_PRESENT_MODE_FIFO_KHR 2U
#define SPEC_VK_IMAGE_USAGE_TRANSFER_DST_BIT 0x00000002U
#define SPEC_VK_IMAGE_USAGE_SAMPLED_BIT 0x00000004U
#define SPEC_VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT 0x00000010U
#define SPEC_VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT 0x00000020U
#define SPEC_VK_SHARING_MODE_EXCLUSIVE 0U
#define SPEC_VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR 0x00000001U
#define SPEC_VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR 0x00000001U
#define SPEC_VK_IMAGE_TYPE_2D 1U
#define SPEC_VK_IMAGE_TILING_OPTIMAL 0U
#define SPEC_VK_IMAGE_LAYOUT_UNDEFINED 0U
#define SPEC_VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL 2U
#define SPEC_VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL 3U
#define SPEC_VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL 5U
#define SPEC_VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL 7U
#define SPEC_VK_IMAGE_LAYOUT_PRESENT_SRC_KHR 1000001002U
#define SPEC_VK_IMAGE_VIEW_TYPE_2D 1U
#define SPEC_VK_IMAGE_ASPECT_COLOR_BIT 0x00000001U
#define SPEC_VK_IMAGE_ASPECT_DEPTH_BIT 0x00000002U
#define SPEC_VK_SAMPLE_COUNT_1_BIT 0x00000001U
#define SPEC_VK_ATTACHMENT_LOAD_OP_CLEAR 1U
#define SPEC_VK_ATTACHMENT_LOAD_OP_DONT_CARE 2U
#define SPEC_VK_ATTACHMENT_STORE_OP_STORE 0U
#define SPEC_VK_ATTACHMENT_STORE_OP_DONT_CARE 1U
#define SPEC_VK_PIPELINE_BIND_POINT_GRAPHICS 0U
#define SPEC_VK_SUBPASS_EXTERNAL (~0U)
#define SPEC_VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT 0x00000400U
#define SPEC_VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT 0x00000100U
#define SPEC_VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT 0x00000100U
#define SPEC_VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT 0x00000400U
#define SPEC_VK_SHADER_STAGE_VERTEX_BIT 0x00000001U
#define SPEC_VK_SHADER_STAGE_FRAGMENT_BIT 0x00000010U
#define SPEC_VK_VERTEX_INPUT_RATE_VERTEX 0U
#define SPEC_VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST 3U
#define SPEC_VK_POLYGON_MODE_FILL 0U
#define SPEC_VK_CULL_MODE_BACK_BIT 0x00000002U
#define SPEC_VK_FRONT_FACE_COUNTER_CLOCKWISE 0U
#define SPEC_VK_COMPARE_OP_LESS 1U
#define SPEC_VK_DYNAMIC_STATE_VIEWPORT 0U
#define SPEC_VK_DYNAMIC_STATE_SCISSOR 1U
#define SPEC_VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT 0x00000002U
#define SPEC_VK_COMMAND_BUFFER_LEVEL_PRIMARY 0U
#define SPEC_VK_FENCE_CREATE_SIGNALED_BIT 0x00000001U
#define SPEC_VK_SUBPASS_CONTENTS_INLINE 0U
#define SPEC_VK_BUFFER_USAGE_TRANSFER_SRC_BIT 0x00000001U
#define SPEC_VK_BUFFER_USAGE_VERTEX_BUFFER_BIT 0x00000080U
#define SPEC_VK_BUFFER_USAGE_INDEX_BUFFER_BIT 0x00000040U
#define SPEC_VK_INDEX_TYPE_UINT16 0U
#define SPEC_VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT 0x00000001U
#define SPEC_VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT 0x00000002U
#define SPEC_VK_MEMORY_PROPERTY_HOST_COHERENT_BIT 0x00000004U
#define SPEC_VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER 1U
#define SPEC_VK_FILTER_LINEAR 1U
#define SPEC_VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE 2U
#define SPEC_VK_BLEND_FACTOR_SRC_ALPHA 6U
#define SPEC_VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA 7U
#define SPEC_VK_BLEND_OP_ADD 0U
#define SPEC_VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT 0x00000001U
#define SPEC_VK_PIPELINE_STAGE_TRANSFER_BIT 0x00001000U
#define SPEC_VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT 0x00000080U
#define SPEC_VK_ACCESS_TRANSFER_WRITE_BIT 0x00001000U
#define SPEC_VK_ACCESS_SHADER_READ_BIT 0x00000020U
#define SPEC_VK_QUEUE_FAMILY_IGNORED (~0U)

typedef struct { uint32_t width, height; } SpecVkExtent2D;
typedef struct { uint32_t width, height, depth; } SpecVkExtent3D;
typedef struct { int32_t x, y; } SpecVkOffset2D;
typedef struct { SpecVkOffset2D offset; SpecVkExtent2D extent; } SpecVkRect2D;
typedef struct { float x, y, width, height, minDepth, maxDepth; } SpecVkViewport;

typedef struct {
    uint32_t sType;
    const void* pNext;
    const char* pApplicationName;
    uint32_t applicationVersion;
    const char* pEngineName;
    uint32_t engineVersion;
    uint32_t apiVersion;
} SpecVkApplicationInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    const SpecVkApplicationInfo* pApplicationInfo;
    uint32_t enabledLayerCount;
    const char* const* ppEnabledLayerNames;
    uint32_t enabledExtensionCount;
    const char* const* ppEnabledExtensionNames;
} SpecVkInstanceCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    void* display;
    void* surface;
} SpecVkWaylandSurfaceCreateInfoKHR;

typedef struct {
    SpecVkFlags queueFlags;
    uint32_t queueCount;
    uint32_t timestampValidBits;
    SpecVkExtent3D minImageTransferGranularity;
} SpecVkQueueFamilyProperties;

typedef struct {
    SpecVkFlags propertyFlags;
    uint32_t heapIndex;
} SpecVkMemoryType;

typedef struct {
    SpecVkDeviceSize size;
    SpecVkFlags flags;
} SpecVkMemoryHeap;

typedef struct {
    uint32_t memoryTypeCount;
    SpecVkMemoryType memoryTypes[32];
    uint32_t memoryHeapCount;
    SpecVkMemoryHeap memoryHeaps[16];
} SpecVkPhysicalDeviceMemoryProperties;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t queueFamilyIndex;
    uint32_t queueCount;
    const float* pQueuePriorities;
} SpecVkDeviceQueueCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t queueCreateInfoCount;
    const SpecVkDeviceQueueCreateInfo* pQueueCreateInfos;
    uint32_t enabledLayerCount;
    const char* const* ppEnabledLayerNames;
    uint32_t enabledExtensionCount;
    const char* const* ppEnabledExtensionNames;
    const void* pEnabledFeatures;
} SpecVkDeviceCreateInfo;

typedef struct {
    uint32_t minImageCount;
    uint32_t maxImageCount;
    SpecVkExtent2D currentExtent;
    SpecVkExtent2D minImageExtent;
    SpecVkExtent2D maxImageExtent;
    uint32_t maxImageArrayLayers;
    SpecVkFlags supportedTransforms;
    uint32_t currentTransform;
    SpecVkFlags supportedCompositeAlpha;
    SpecVkFlags supportedUsageFlags;
} SpecVkSurfaceCapabilitiesKHR;

typedef struct {
    uint32_t format;
    uint32_t colorSpace;
} SpecVkSurfaceFormatKHR;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    SpecVkSurfaceKHR surface;
    uint32_t minImageCount;
    uint32_t imageFormat;
    uint32_t imageColorSpace;
    SpecVkExtent2D imageExtent;
    uint32_t imageArrayLayers;
    SpecVkFlags imageUsage;
    uint32_t imageSharingMode;
    uint32_t queueFamilyIndexCount;
    const uint32_t* pQueueFamilyIndices;
    uint32_t preTransform;
    uint32_t compositeAlpha;
    uint32_t presentMode;
    SpecVkBool32 clipped;
    SpecVkSwapchainKHR oldSwapchain;
} SpecVkSwapchainCreateInfoKHR;

typedef struct {
    uint32_t r, g, b, a;
} SpecVkComponentMapping;

typedef struct {
    SpecVkFlags aspectMask;
    uint32_t baseMipLevel;
    uint32_t levelCount;
    uint32_t baseArrayLayer;
    uint32_t layerCount;
} SpecVkImageSubresourceRange;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    SpecVkImage image;
    uint32_t viewType;
    uint32_t format;
    SpecVkComponentMapping components;
    SpecVkImageSubresourceRange subresourceRange;
} SpecVkImageViewCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t imageType;
    uint32_t format;
    SpecVkExtent3D extent;
    uint32_t mipLevels;
    uint32_t arrayLayers;
    uint32_t samples;
    uint32_t tiling;
    SpecVkFlags usage;
    uint32_t sharingMode;
    uint32_t queueFamilyIndexCount;
    const uint32_t* pQueueFamilyIndices;
    uint32_t initialLayout;
} SpecVkImageCreateInfo;

typedef struct {
    SpecVkDeviceSize size;
    SpecVkDeviceSize alignment;
    uint32_t memoryTypeBits;
} SpecVkMemoryRequirements;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkDeviceSize allocationSize;
    uint32_t memoryTypeIndex;
} SpecVkMemoryAllocateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    SpecVkDeviceSize size;
    SpecVkFlags usage;
    uint32_t sharingMode;
    uint32_t queueFamilyIndexCount;
    const uint32_t* pQueueFamilyIndices;
} SpecVkBufferCreateInfo;

typedef struct {
    SpecVkFlags flags;
    uint32_t format;
    uint32_t samples;
    uint32_t loadOp;
    uint32_t storeOp;
    uint32_t stencilLoadOp;
    uint32_t stencilStoreOp;
    uint32_t initialLayout;
    uint32_t finalLayout;
} SpecVkAttachmentDescription;

typedef struct {
    uint32_t attachment;
    uint32_t layout;
} SpecVkAttachmentReference;

typedef struct {
    SpecVkFlags flags;
    uint32_t pipelineBindPoint;
    uint32_t inputAttachmentCount;
    const SpecVkAttachmentReference* pInputAttachments;
    uint32_t colorAttachmentCount;
    const SpecVkAttachmentReference* pColorAttachments;
    const SpecVkAttachmentReference* pResolveAttachments;
    const SpecVkAttachmentReference* pDepthStencilAttachment;
    uint32_t preserveAttachmentCount;
    const uint32_t* pPreserveAttachments;
} SpecVkSubpassDescription;

typedef struct {
    uint32_t srcSubpass;
    uint32_t dstSubpass;
    SpecVkFlags srcStageMask;
    SpecVkFlags dstStageMask;
    SpecVkFlags srcAccessMask;
    SpecVkFlags dstAccessMask;
    SpecVkFlags dependencyFlags;
} SpecVkSubpassDependency;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t attachmentCount;
    const SpecVkAttachmentDescription* pAttachments;
    uint32_t subpassCount;
    const SpecVkSubpassDescription* pSubpasses;
    uint32_t dependencyCount;
    const SpecVkSubpassDependency* pDependencies;
} SpecVkRenderPassCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    size_t codeSize;
    const uint32_t* pCode;
} SpecVkShaderModuleCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t stage;
    SpecVkShaderModule module;
    const char* pName;
    const void* pSpecializationInfo;
} SpecVkPipelineShaderStageCreateInfo;

typedef struct {
    uint32_t binding;
    uint32_t stride;
    uint32_t inputRate;
} SpecVkVertexInputBindingDescription;

typedef struct {
    uint32_t location;
    uint32_t binding;
    uint32_t format;
    uint32_t offset;
} SpecVkVertexInputAttributeDescription;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t vertexBindingDescriptionCount;
    const SpecVkVertexInputBindingDescription* pVertexBindingDescriptions;
    uint32_t vertexAttributeDescriptionCount;
    const SpecVkVertexInputAttributeDescription* pVertexAttributeDescriptions;
} SpecVkPipelineVertexInputStateCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t topology;
    SpecVkBool32 primitiveRestartEnable;
} SpecVkPipelineInputAssemblyStateCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t viewportCount;
    const SpecVkViewport* pViewports;
    uint32_t scissorCount;
    const SpecVkRect2D* pScissors;
} SpecVkPipelineViewportStateCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    SpecVkBool32 depthClampEnable;
    SpecVkBool32 rasterizerDiscardEnable;
    uint32_t polygonMode;
    SpecVkFlags cullMode;
    uint32_t frontFace;
    SpecVkBool32 depthBiasEnable;
    float depthBiasConstantFactor;
    float depthBiasClamp;
    float depthBiasSlopeFactor;
    float lineWidth;
} SpecVkPipelineRasterizationStateCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t rasterizationSamples;
    SpecVkBool32 sampleShadingEnable;
    float minSampleShading;
    const uint32_t* pSampleMask;
    SpecVkBool32 alphaToCoverageEnable;
    SpecVkBool32 alphaToOneEnable;
} SpecVkPipelineMultisampleStateCreateInfo;

typedef struct {
    uint32_t failOp, passOp, depthFailOp, compareOp, compareMask, writeMask, reference;
} SpecVkStencilOpState;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    SpecVkBool32 depthTestEnable;
    SpecVkBool32 depthWriteEnable;
    uint32_t depthCompareOp;
    SpecVkBool32 depthBoundsTestEnable;
    SpecVkBool32 stencilTestEnable;
    SpecVkStencilOpState front;
    SpecVkStencilOpState back;
    float minDepthBounds;
    float maxDepthBounds;
} SpecVkPipelineDepthStencilStateCreateInfo;

typedef struct {
    SpecVkBool32 blendEnable;
    uint32_t srcColorBlendFactor;
    uint32_t dstColorBlendFactor;
    uint32_t colorBlendOp;
    uint32_t srcAlphaBlendFactor;
    uint32_t dstAlphaBlendFactor;
    uint32_t alphaBlendOp;
    SpecVkFlags colorWriteMask;
} SpecVkPipelineColorBlendAttachmentState;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    SpecVkBool32 logicOpEnable;
    uint32_t logicOp;
    uint32_t attachmentCount;
    const SpecVkPipelineColorBlendAttachmentState* pAttachments;
    float blendConstants[4];
} SpecVkPipelineColorBlendStateCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t dynamicStateCount;
    const uint32_t* pDynamicStates;
} SpecVkPipelineDynamicStateCreateInfo;

typedef struct {
    SpecVkFlags stageFlags;
    uint32_t offset;
    uint32_t size;
} SpecVkPushConstantRange;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t setLayoutCount;
    const void* pSetLayouts;
    uint32_t pushConstantRangeCount;
    const SpecVkPushConstantRange* pPushConstantRanges;
} SpecVkPipelineLayoutCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t stageCount;
    const SpecVkPipelineShaderStageCreateInfo* pStages;
    const SpecVkPipelineVertexInputStateCreateInfo* pVertexInputState;
    const SpecVkPipelineInputAssemblyStateCreateInfo* pInputAssemblyState;
    const void* pTessellationState;
    const SpecVkPipelineViewportStateCreateInfo* pViewportState;
    const SpecVkPipelineRasterizationStateCreateInfo* pRasterizationState;
    const SpecVkPipelineMultisampleStateCreateInfo* pMultisampleState;
    const SpecVkPipelineDepthStencilStateCreateInfo* pDepthStencilState;
    const SpecVkPipelineColorBlendStateCreateInfo* pColorBlendState;
    const SpecVkPipelineDynamicStateCreateInfo* pDynamicState;
    SpecVkPipelineLayout layout;
    SpecVkRenderPass renderPass;
    uint32_t subpass;
    SpecVkPipeline basePipelineHandle;
    int32_t basePipelineIndex;
} SpecVkGraphicsPipelineCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    SpecVkRenderPass renderPass;
    uint32_t attachmentCount;
    const SpecVkImageView* pAttachments;
    uint32_t width;
    uint32_t height;
    uint32_t layers;
} SpecVkFramebufferCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t queueFamilyIndex;
} SpecVkCommandPoolCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkCommandPool commandPool;
    uint32_t level;
    uint32_t commandBufferCount;
} SpecVkCommandBufferAllocateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    const void* pInheritanceInfo;
} SpecVkCommandBufferBeginInfo;

typedef union {
    float float32[4];
    int32_t int32[4];
    uint32_t uint32[4];
    struct { float depth; uint32_t stencil; } depthStencil;
} SpecVkClearValue;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkRenderPass renderPass;
    SpecVkFramebuffer framebuffer;
    SpecVkRect2D renderArea;
    uint32_t clearValueCount;
    const SpecVkClearValue* pClearValues;
} SpecVkRenderPassBeginInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
} SpecVkSemaphoreCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
} SpecVkFenceCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    uint32_t waitSemaphoreCount;
    const SpecVkSemaphore* pWaitSemaphores;
    const SpecVkFlags* pWaitDstStageMask;
    uint32_t commandBufferCount;
    const SpecVkCommandBuffer* pCommandBuffers;
    uint32_t signalSemaphoreCount;
    const SpecVkSemaphore* pSignalSemaphores;
} SpecVkSubmitInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    uint32_t waitSemaphoreCount;
    const SpecVkSemaphore* pWaitSemaphores;
    uint32_t swapchainCount;
    const SpecVkSwapchainKHR* pSwapchains;
    const uint32_t* pImageIndices;
    SpecVkResult* pResults;
} SpecVkPresentInfoKHR;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t magFilter, minFilter, mipmapMode;
    uint32_t addressModeU, addressModeV, addressModeW;
    float mipLodBias;
    SpecVkBool32 anisotropyEnable;
    float maxAnisotropy;
    SpecVkBool32 compareEnable;
    uint32_t compareOp;
    float minLod, maxLod;
    uint32_t borderColor;
    SpecVkBool32 unnormalizedCoordinates;
} SpecVkSamplerCreateInfo;

typedef struct {
    uint32_t binding;
    uint32_t descriptorType;
    uint32_t descriptorCount;
    SpecVkFlags stageFlags;
    const SpecVkSampler* pImmutableSamplers;
} SpecVkDescriptorSetLayoutBinding;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t bindingCount;
    const SpecVkDescriptorSetLayoutBinding* pBindings;
} SpecVkDescriptorSetLayoutCreateInfo;

typedef struct {
    uint32_t type;
    uint32_t descriptorCount;
} SpecVkDescriptorPoolSize;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags flags;
    uint32_t maxSets;
    uint32_t poolSizeCount;
    const SpecVkDescriptorPoolSize* pPoolSizes;
} SpecVkDescriptorPoolCreateInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkDescriptorPool descriptorPool;
    uint32_t descriptorSetCount;
    const SpecVkDescriptorSetLayout* pSetLayouts;
} SpecVkDescriptorSetAllocateInfo;

typedef struct {
    SpecVkSampler sampler;
    SpecVkImageView imageView;
    uint32_t imageLayout;
} SpecVkDescriptorImageInfo;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkDescriptorSet dstSet;
    uint32_t dstBinding;
    uint32_t dstArrayElement;
    uint32_t descriptorCount;
    uint32_t descriptorType;
    const SpecVkDescriptorImageInfo* pImageInfo;
    const void* pBufferInfo;
    const void* pTexelBufferView;
} SpecVkWriteDescriptorSet;

typedef struct {
    uint32_t sType;
    const void* pNext;
    SpecVkFlags srcAccessMask;
    SpecVkFlags dstAccessMask;
    uint32_t oldLayout;
    uint32_t newLayout;
    uint32_t srcQueueFamilyIndex;
    uint32_t dstQueueFamilyIndex;
    SpecVkImage image;
    SpecVkImageSubresourceRange subresourceRange;
} SpecVkImageMemoryBarrier;

typedef struct {
    SpecVkDeviceSize bufferOffset;
    uint32_t bufferRowLength;
    uint32_t bufferImageHeight;
    struct { SpecVkFlags aspectMask; uint32_t mipLevel; uint32_t baseArrayLayer; uint32_t layerCount; } imageSubresource;
    struct { int32_t x, y, z; } imageOffset;
    SpecVkExtent3D imageExtent;
} SpecVkBufferImageCopy;

/* Function pointer types */
typedef void* (*PFN_spec_vkGetInstanceProcAddr)(SpecVkInstance, const char*);
typedef void* (*PFN_spec_vkGetDeviceProcAddr)(SpecVkDevice, const char*);
typedef SpecVkResult (*PFN_spec_vkCreateInstance)(const SpecVkInstanceCreateInfo*, const void*, SpecVkInstance*);
typedef void (*PFN_spec_vkDestroyInstance)(SpecVkInstance, const void*);
typedef SpecVkResult (*PFN_spec_vkCreateWaylandSurfaceKHR)(SpecVkInstance, const SpecVkWaylandSurfaceCreateInfoKHR*, const void*, SpecVkSurfaceKHR*);
typedef void (*PFN_spec_vkDestroySurfaceKHR)(SpecVkInstance, SpecVkSurfaceKHR, const void*);
typedef SpecVkResult (*PFN_spec_vkEnumeratePhysicalDevices)(SpecVkInstance, uint32_t*, SpecVkPhysicalDevice*);
typedef void (*PFN_spec_vkGetPhysicalDeviceQueueFamilyProperties)(SpecVkPhysicalDevice, uint32_t*, SpecVkQueueFamilyProperties*);
typedef SpecVkResult (*PFN_spec_vkGetPhysicalDeviceSurfaceSupportKHR)(SpecVkPhysicalDevice, uint32_t, SpecVkSurfaceKHR, SpecVkBool32*);
typedef void (*PFN_spec_vkGetPhysicalDeviceMemoryProperties)(SpecVkPhysicalDevice, SpecVkPhysicalDeviceMemoryProperties*);
typedef SpecVkResult (*PFN_spec_vkGetPhysicalDeviceSurfaceCapabilitiesKHR)(SpecVkPhysicalDevice, SpecVkSurfaceKHR, SpecVkSurfaceCapabilitiesKHR*);
typedef SpecVkResult (*PFN_spec_vkGetPhysicalDeviceSurfaceFormatsKHR)(SpecVkPhysicalDevice, SpecVkSurfaceKHR, uint32_t*, SpecVkSurfaceFormatKHR*);
typedef SpecVkResult (*PFN_spec_vkCreateDevice)(SpecVkPhysicalDevice, const SpecVkDeviceCreateInfo*, const void*, SpecVkDevice*);
typedef void (*PFN_spec_vkDestroyDevice)(SpecVkDevice, const void*);
typedef void (*PFN_spec_vkGetDeviceQueue)(SpecVkDevice, uint32_t, uint32_t, SpecVkQueue*);
typedef SpecVkResult (*PFN_spec_vkDeviceWaitIdle)(SpecVkDevice);
typedef SpecVkResult (*PFN_spec_vkCreateSwapchainKHR)(SpecVkDevice, const SpecVkSwapchainCreateInfoKHR*, const void*, SpecVkSwapchainKHR*);
typedef void (*PFN_spec_vkDestroySwapchainKHR)(SpecVkDevice, SpecVkSwapchainKHR, const void*);
typedef SpecVkResult (*PFN_spec_vkGetSwapchainImagesKHR)(SpecVkDevice, SpecVkSwapchainKHR, uint32_t*, SpecVkImage*);
typedef SpecVkResult (*PFN_spec_vkAcquireNextImageKHR)(SpecVkDevice, SpecVkSwapchainKHR, uint64_t, SpecVkSemaphore, SpecVkFence, uint32_t*);
typedef SpecVkResult (*PFN_spec_vkQueuePresentKHR)(SpecVkQueue, const SpecVkPresentInfoKHR*);
typedef SpecVkResult (*PFN_spec_vkCreateImageView)(SpecVkDevice, const SpecVkImageViewCreateInfo*, const void*, SpecVkImageView*);
typedef void (*PFN_spec_vkDestroyImageView)(SpecVkDevice, SpecVkImageView, const void*);
typedef SpecVkResult (*PFN_spec_vkCreateImage)(SpecVkDevice, const SpecVkImageCreateInfo*, const void*, SpecVkImage*);
typedef void (*PFN_spec_vkDestroyImage)(SpecVkDevice, SpecVkImage, const void*);
typedef void (*PFN_spec_vkGetImageMemoryRequirements)(SpecVkDevice, SpecVkImage, SpecVkMemoryRequirements*);
typedef SpecVkResult (*PFN_spec_vkAllocateMemory)(SpecVkDevice, const SpecVkMemoryAllocateInfo*, const void*, SpecVkDeviceMemory*);
typedef void (*PFN_spec_vkFreeMemory)(SpecVkDevice, SpecVkDeviceMemory, const void*);
typedef SpecVkResult (*PFN_spec_vkBindImageMemory)(SpecVkDevice, SpecVkImage, SpecVkDeviceMemory, SpecVkDeviceSize);
typedef SpecVkResult (*PFN_spec_vkCreateBuffer)(SpecVkDevice, const SpecVkBufferCreateInfo*, const void*, SpecVkBuffer*);
typedef void (*PFN_spec_vkDestroyBuffer)(SpecVkDevice, SpecVkBuffer, const void*);
typedef void (*PFN_spec_vkGetBufferMemoryRequirements)(SpecVkDevice, SpecVkBuffer, SpecVkMemoryRequirements*);
typedef SpecVkResult (*PFN_spec_vkBindBufferMemory)(SpecVkDevice, SpecVkBuffer, SpecVkDeviceMemory, SpecVkDeviceSize);
typedef SpecVkResult (*PFN_spec_vkMapMemory)(SpecVkDevice, SpecVkDeviceMemory, SpecVkDeviceSize, SpecVkDeviceSize, SpecVkFlags, void**);
typedef void (*PFN_spec_vkUnmapMemory)(SpecVkDevice, SpecVkDeviceMemory);
typedef SpecVkResult (*PFN_spec_vkCreateRenderPass)(SpecVkDevice, const SpecVkRenderPassCreateInfo*, const void*, SpecVkRenderPass*);
typedef void (*PFN_spec_vkDestroyRenderPass)(SpecVkDevice, SpecVkRenderPass, const void*);
typedef SpecVkResult (*PFN_spec_vkCreateShaderModule)(SpecVkDevice, const SpecVkShaderModuleCreateInfo*, const void*, SpecVkShaderModule*);
typedef void (*PFN_spec_vkDestroyShaderModule)(SpecVkDevice, SpecVkShaderModule, const void*);
typedef SpecVkResult (*PFN_spec_vkCreatePipelineLayout)(SpecVkDevice, const SpecVkPipelineLayoutCreateInfo*, const void*, SpecVkPipelineLayout*);
typedef void (*PFN_spec_vkDestroyPipelineLayout)(SpecVkDevice, SpecVkPipelineLayout, const void*);
typedef SpecVkResult (*PFN_spec_vkCreateGraphicsPipelines)(SpecVkDevice, SpecVkPipelineCache, uint32_t, const SpecVkGraphicsPipelineCreateInfo*, const void*, SpecVkPipeline*);
typedef void (*PFN_spec_vkDestroyPipeline)(SpecVkDevice, SpecVkPipeline, const void*);
typedef SpecVkResult (*PFN_spec_vkCreateFramebuffer)(SpecVkDevice, const SpecVkFramebufferCreateInfo*, const void*, SpecVkFramebuffer*);
typedef void (*PFN_spec_vkDestroyFramebuffer)(SpecVkDevice, SpecVkFramebuffer, const void*);
typedef SpecVkResult (*PFN_spec_vkCreateCommandPool)(SpecVkDevice, const SpecVkCommandPoolCreateInfo*, const void*, SpecVkCommandPool*);
typedef void (*PFN_spec_vkDestroyCommandPool)(SpecVkDevice, SpecVkCommandPool, const void*);
typedef SpecVkResult (*PFN_spec_vkAllocateCommandBuffers)(SpecVkDevice, const SpecVkCommandBufferAllocateInfo*, SpecVkCommandBuffer*);
typedef SpecVkResult (*PFN_spec_vkResetCommandBuffer)(SpecVkCommandBuffer, SpecVkFlags);
typedef SpecVkResult (*PFN_spec_vkBeginCommandBuffer)(SpecVkCommandBuffer, const SpecVkCommandBufferBeginInfo*);
typedef SpecVkResult (*PFN_spec_vkEndCommandBuffer)(SpecVkCommandBuffer);
typedef void (*PFN_spec_vkCmdBeginRenderPass)(SpecVkCommandBuffer, const SpecVkRenderPassBeginInfo*, uint32_t);
typedef void (*PFN_spec_vkCmdEndRenderPass)(SpecVkCommandBuffer);
typedef void (*PFN_spec_vkCmdBindPipeline)(SpecVkCommandBuffer, uint32_t, SpecVkPipeline);
typedef void (*PFN_spec_vkCmdSetViewport)(SpecVkCommandBuffer, uint32_t, uint32_t, const SpecVkViewport*);
typedef void (*PFN_spec_vkCmdSetScissor)(SpecVkCommandBuffer, uint32_t, uint32_t, const SpecVkRect2D*);
typedef void (*PFN_spec_vkCmdBindVertexBuffers)(SpecVkCommandBuffer, uint32_t, uint32_t, const SpecVkBuffer*, const SpecVkDeviceSize*);
typedef void (*PFN_spec_vkCmdBindIndexBuffer)(SpecVkCommandBuffer, SpecVkBuffer, SpecVkDeviceSize, uint32_t);
typedef void (*PFN_spec_vkCmdPushConstants)(SpecVkCommandBuffer, SpecVkPipelineLayout, SpecVkFlags, uint32_t, uint32_t, const void*);
typedef void (*PFN_spec_vkCmdDrawIndexed)(SpecVkCommandBuffer, uint32_t, uint32_t, uint32_t, int32_t, uint32_t);
typedef SpecVkResult (*PFN_spec_vkCreateSemaphore)(SpecVkDevice, const SpecVkSemaphoreCreateInfo*, const void*, SpecVkSemaphore*);
typedef void (*PFN_spec_vkDestroySemaphore)(SpecVkDevice, SpecVkSemaphore, const void*);
typedef SpecVkResult (*PFN_spec_vkCreateFence)(SpecVkDevice, const SpecVkFenceCreateInfo*, const void*, SpecVkFence*);
typedef void (*PFN_spec_vkDestroyFence)(SpecVkDevice, SpecVkFence, const void*);
typedef SpecVkResult (*PFN_spec_vkWaitForFences)(SpecVkDevice, uint32_t, const SpecVkFence*, SpecVkBool32, uint64_t);
typedef SpecVkResult (*PFN_spec_vkResetFences)(SpecVkDevice, uint32_t, const SpecVkFence*);
typedef SpecVkResult (*PFN_spec_vkQueueSubmit)(SpecVkQueue, uint32_t, const SpecVkSubmitInfo*, SpecVkFence);
typedef SpecVkResult (*PFN_spec_vkCreateSampler)(SpecVkDevice, const SpecVkSamplerCreateInfo*, const void*, SpecVkSampler*);
typedef void (*PFN_spec_vkDestroySampler)(SpecVkDevice, SpecVkSampler, const void*);
typedef SpecVkResult (*PFN_spec_vkCreateDescriptorSetLayout)(SpecVkDevice, const SpecVkDescriptorSetLayoutCreateInfo*, const void*, SpecVkDescriptorSetLayout*);
typedef void (*PFN_spec_vkDestroyDescriptorSetLayout)(SpecVkDevice, SpecVkDescriptorSetLayout, const void*);
typedef SpecVkResult (*PFN_spec_vkCreateDescriptorPool)(SpecVkDevice, const SpecVkDescriptorPoolCreateInfo*, const void*, SpecVkDescriptorPool*);
typedef void (*PFN_spec_vkDestroyDescriptorPool)(SpecVkDevice, SpecVkDescriptorPool, const void*);
typedef SpecVkResult (*PFN_spec_vkAllocateDescriptorSets)(SpecVkDevice, const SpecVkDescriptorSetAllocateInfo*, SpecVkDescriptorSet*);
typedef void (*PFN_spec_vkUpdateDescriptorSets)(SpecVkDevice, uint32_t, const SpecVkWriteDescriptorSet*, uint32_t, const void*);
typedef void (*PFN_spec_vkCmdBindDescriptorSets)(SpecVkCommandBuffer, uint32_t, SpecVkPipelineLayout, uint32_t, uint32_t, const SpecVkDescriptorSet*, uint32_t, const uint32_t*);
typedef void (*PFN_spec_vkCmdDraw)(SpecVkCommandBuffer, uint32_t, uint32_t, uint32_t, uint32_t);
typedef void (*PFN_spec_vkCmdPipelineBarrier)(SpecVkCommandBuffer, SpecVkFlags, SpecVkFlags, SpecVkFlags, uint32_t, const void*, uint32_t, const void*, uint32_t, const SpecVkImageMemoryBarrier*);
typedef void (*PFN_spec_vkCmdCopyBufferToImage)(SpecVkCommandBuffer, SpecVkBuffer, SpecVkImage, uint32_t, uint32_t, const SpecVkBufferImageCopy*);

typedef struct {
    void* lib;
    PFN_spec_vkGetInstanceProcAddr vkGetInstanceProcAddr;
    PFN_spec_vkGetDeviceProcAddr vkGetDeviceProcAddr;
    PFN_spec_vkCreateInstance vkCreateInstance;
    PFN_spec_vkDestroyInstance vkDestroyInstance;
    PFN_spec_vkCreateWaylandSurfaceKHR vkCreateWaylandSurfaceKHR;
    PFN_spec_vkDestroySurfaceKHR vkDestroySurfaceKHR;
    PFN_spec_vkEnumeratePhysicalDevices vkEnumeratePhysicalDevices;
    PFN_spec_vkGetPhysicalDeviceQueueFamilyProperties vkGetPhysicalDeviceQueueFamilyProperties;
    PFN_spec_vkGetPhysicalDeviceSurfaceSupportKHR vkGetPhysicalDeviceSurfaceSupportKHR;
    PFN_spec_vkGetPhysicalDeviceMemoryProperties vkGetPhysicalDeviceMemoryProperties;
    PFN_spec_vkGetPhysicalDeviceSurfaceCapabilitiesKHR vkGetPhysicalDeviceSurfaceCapabilitiesKHR;
    PFN_spec_vkGetPhysicalDeviceSurfaceFormatsKHR vkGetPhysicalDeviceSurfaceFormatsKHR;
    PFN_spec_vkCreateDevice vkCreateDevice;
    PFN_spec_vkDestroyDevice vkDestroyDevice;
    PFN_spec_vkGetDeviceQueue vkGetDeviceQueue;
    PFN_spec_vkDeviceWaitIdle vkDeviceWaitIdle;
    PFN_spec_vkCreateSwapchainKHR vkCreateSwapchainKHR;
    PFN_spec_vkDestroySwapchainKHR vkDestroySwapchainKHR;
    PFN_spec_vkGetSwapchainImagesKHR vkGetSwapchainImagesKHR;
    PFN_spec_vkAcquireNextImageKHR vkAcquireNextImageKHR;
    PFN_spec_vkQueuePresentKHR vkQueuePresentKHR;
    PFN_spec_vkCreateImageView vkCreateImageView;
    PFN_spec_vkDestroyImageView vkDestroyImageView;
    PFN_spec_vkCreateImage vkCreateImage;
    PFN_spec_vkDestroyImage vkDestroyImage;
    PFN_spec_vkGetImageMemoryRequirements vkGetImageMemoryRequirements;
    PFN_spec_vkAllocateMemory vkAllocateMemory;
    PFN_spec_vkFreeMemory vkFreeMemory;
    PFN_spec_vkBindImageMemory vkBindImageMemory;
    PFN_spec_vkCreateBuffer vkCreateBuffer;
    PFN_spec_vkDestroyBuffer vkDestroyBuffer;
    PFN_spec_vkGetBufferMemoryRequirements vkGetBufferMemoryRequirements;
    PFN_spec_vkBindBufferMemory vkBindBufferMemory;
    PFN_spec_vkMapMemory vkMapMemory;
    PFN_spec_vkUnmapMemory vkUnmapMemory;
    PFN_spec_vkCreateRenderPass vkCreateRenderPass;
    PFN_spec_vkDestroyRenderPass vkDestroyRenderPass;
    PFN_spec_vkCreateShaderModule vkCreateShaderModule;
    PFN_spec_vkDestroyShaderModule vkDestroyShaderModule;
    PFN_spec_vkCreatePipelineLayout vkCreatePipelineLayout;
    PFN_spec_vkDestroyPipelineLayout vkDestroyPipelineLayout;
    PFN_spec_vkCreateGraphicsPipelines vkCreateGraphicsPipelines;
    PFN_spec_vkDestroyPipeline vkDestroyPipeline;
    PFN_spec_vkCreateFramebuffer vkCreateFramebuffer;
    PFN_spec_vkDestroyFramebuffer vkDestroyFramebuffer;
    PFN_spec_vkCreateCommandPool vkCreateCommandPool;
    PFN_spec_vkDestroyCommandPool vkDestroyCommandPool;
    PFN_spec_vkAllocateCommandBuffers vkAllocateCommandBuffers;
    PFN_spec_vkResetCommandBuffer vkResetCommandBuffer;
    PFN_spec_vkBeginCommandBuffer vkBeginCommandBuffer;
    PFN_spec_vkEndCommandBuffer vkEndCommandBuffer;
    PFN_spec_vkCmdBeginRenderPass vkCmdBeginRenderPass;
    PFN_spec_vkCmdEndRenderPass vkCmdEndRenderPass;
    PFN_spec_vkCmdBindPipeline vkCmdBindPipeline;
    PFN_spec_vkCmdSetViewport vkCmdSetViewport;
    PFN_spec_vkCmdSetScissor vkCmdSetScissor;
    PFN_spec_vkCmdBindVertexBuffers vkCmdBindVertexBuffers;
    PFN_spec_vkCmdBindIndexBuffer vkCmdBindIndexBuffer;
    PFN_spec_vkCmdPushConstants vkCmdPushConstants;
    PFN_spec_vkCmdDrawIndexed vkCmdDrawIndexed;
    PFN_spec_vkCreateSemaphore vkCreateSemaphore;
    PFN_spec_vkDestroySemaphore vkDestroySemaphore;
    PFN_spec_vkCreateFence vkCreateFence;
    PFN_spec_vkDestroyFence vkDestroyFence;
    PFN_spec_vkWaitForFences vkWaitForFences;
    PFN_spec_vkResetFences vkResetFences;
    PFN_spec_vkQueueSubmit vkQueueSubmit;
    PFN_spec_vkCreateSampler vkCreateSampler;
    PFN_spec_vkDestroySampler vkDestroySampler;
    PFN_spec_vkCreateDescriptorSetLayout vkCreateDescriptorSetLayout;
    PFN_spec_vkDestroyDescriptorSetLayout vkDestroyDescriptorSetLayout;
    PFN_spec_vkCreateDescriptorPool vkCreateDescriptorPool;
    PFN_spec_vkDestroyDescriptorPool vkDestroyDescriptorPool;
    PFN_spec_vkAllocateDescriptorSets vkAllocateDescriptorSets;
    PFN_spec_vkUpdateDescriptorSets vkUpdateDescriptorSets;
    PFN_spec_vkCmdBindDescriptorSets vkCmdBindDescriptorSets;
    PFN_spec_vkCmdDraw vkCmdDraw;
    PFN_spec_vkCmdPipelineBarrier vkCmdPipelineBarrier;
    PFN_spec_vkCmdCopyBufferToImage vkCmdCopyBufferToImage;

    SpecVkInstance instance;
    SpecVkSurfaceKHR surface;
    SpecVkPhysicalDevice phys;
    SpecVkDevice device;
    SpecVkQueue queue;
    uint32_t queue_family;

    uint32_t color_format;
    uint32_t color_space;
    SpecVkExtent2D extent;
    SpecVkSwapchainKHR swapchain;
    uint32_t image_count;
    SpecVkImage* swap_images;
    SpecVkImageView* swap_views;
    SpecVkFramebuffer* framebuffers;

    SpecVkImage depth_image;
    SpecVkDeviceMemory depth_mem;
    SpecVkImageView depth_view;

    SpecVkRenderPass render_pass;
    SpecVkShaderModule vert_mod;
    SpecVkShaderModule frag_mod;
    SpecVkPipelineLayout pipe_layout;
    SpecVkPipeline pipeline;

    SpecVkCommandPool cmd_pool;
    SpecVkCommandBuffer cmd_buf[2];
    SpecVkSemaphore img_avail_sem[2];
    SpecVkSemaphore render_done_sem[2];
    SpecVkFence in_flight_fence[2];
    uint32_t cur_frame;

    SpecVkBuffer vertex_buf;
    SpecVkDeviceMemory vertex_mem;
    SpecVkBuffer index_buf;
    SpecVkDeviceMemory index_mem;
    uint32_t index_count;

    SpecVkDescriptorSetLayout overlay_desc_layout;
    SpecVkDescriptorPool overlay_desc_pool;
    SpecVkDescriptorSet overlay_desc_set;
    SpecVkSampler overlay_sampler;
    SpecVkShaderModule overlay_vert_mod;
    SpecVkShaderModule overlay_frag_mod;
    SpecVkPipelineLayout overlay_pipe_layout;
    SpecVkPipeline overlay_pipeline;
    SpecVkBuffer overlay_vbuf;
    SpecVkDeviceMemory overlay_vmem;
    SpecVkImage overlay_img;
    SpecVkDeviceMemory overlay_mem;
    SpecVkImageView overlay_view;
    SpecVkBuffer overlay_staging_buf[2];
    SpecVkDeviceMemory overlay_staging_mem[2];
    uint8_t* overlay_cpu_buf;
    size_t overlay_cpu_bytes;
    uint32_t overlay_w;
    uint32_t overlay_h;
    uint32_t overlay_img_w;
    uint32_t overlay_img_h;
    uint32_t overlay_img_layout;
    int overlay_dirty;
    int overlay_ready;
    int32_t vp_x;
    int32_t vp_y;
    uint32_t vp_w;
    uint32_t vp_h;
    float clear_r;
    float clear_g;
    float clear_b;
    float clear_a;
} SpecVulkanCtx;

static char _spec_vk_error[256] = {0};

static void _spec_vk_set_error(const char* msg) {
    if (!msg) { _spec_vk_error[0] = 0; return; }
    snprintf(_spec_vk_error, sizeof(_spec_vk_error), "%s", msg);
}

static uint32_t _spec_vk_find_memory_type(SpecVulkanCtx* ctx, uint32_t type_filter, uint32_t props) {
    SpecVkPhysicalDeviceMemoryProperties mp;
    ctx->vkGetPhysicalDeviceMemoryProperties(ctx->phys, &mp);
    for (uint32_t i = 0; i < mp.memoryTypeCount; i++) {
        if ((type_filter & (1U << i)) && ((mp.memoryTypes[i].propertyFlags & props) == props)) {
            return i;
        }
    }
    return ~0U;
}

static int _spec_vk_load_procs(SpecVulkanCtx* ctx) {
    ctx->lib = dlopen("libvulkan.so.1", RTLD_NOW | RTLD_LOCAL);
    if (!ctx->lib) {
        _spec_vk_set_error("dlopen(libvulkan.so.1) failed");
        return 0;
    }
    ctx->vkGetInstanceProcAddr = (PFN_spec_vkGetInstanceProcAddr)dlsym(ctx->lib, "vkGetInstanceProcAddr");
    if (!ctx->vkGetInstanceProcAddr) {
        _spec_vk_set_error("vkGetInstanceProcAddr not found");
        return 0;
    }
    ctx->vkCreateInstance = (PFN_spec_vkCreateInstance)ctx->vkGetInstanceProcAddr(NULL, "vkCreateInstance");
    return ctx->vkCreateInstance != NULL;
}

static int _spec_vk_load_instance_procs(SpecVulkanCtx* ctx) {
    SpecVkInstance inst = ctx->instance;
    #define LOAD_IPROC(fn) do { \
        ctx->fn = (PFN_spec_##fn)ctx->vkGetInstanceProcAddr(inst, #fn); \
        if (!ctx->fn) { _spec_vk_set_error("Missing Vulkan proc: " #fn); return 0; } \
    } while (0)
    LOAD_IPROC(vkDestroyInstance);
    LOAD_IPROC(vkCreateWaylandSurfaceKHR);
    LOAD_IPROC(vkDestroySurfaceKHR);
    LOAD_IPROC(vkEnumeratePhysicalDevices);
    LOAD_IPROC(vkGetPhysicalDeviceQueueFamilyProperties);
    LOAD_IPROC(vkGetPhysicalDeviceSurfaceSupportKHR);
    LOAD_IPROC(vkGetPhysicalDeviceMemoryProperties);
    LOAD_IPROC(vkGetPhysicalDeviceSurfaceCapabilitiesKHR);
    LOAD_IPROC(vkGetPhysicalDeviceSurfaceFormatsKHR);
    LOAD_IPROC(vkCreateDevice);
    LOAD_IPROC(vkDestroyDevice);
    LOAD_IPROC(vkGetDeviceQueue);
    LOAD_IPROC(vkDeviceWaitIdle);
    LOAD_IPROC(vkCreateSwapchainKHR);
    LOAD_IPROC(vkDestroySwapchainKHR);
    LOAD_IPROC(vkGetSwapchainImagesKHR);
    LOAD_IPROC(vkAcquireNextImageKHR);
    LOAD_IPROC(vkQueuePresentKHR);
    LOAD_IPROC(vkCreateImageView);
    LOAD_IPROC(vkDestroyImageView);
    LOAD_IPROC(vkCreateImage);
    LOAD_IPROC(vkDestroyImage);
    LOAD_IPROC(vkGetImageMemoryRequirements);
    LOAD_IPROC(vkAllocateMemory);
    LOAD_IPROC(vkFreeMemory);
    LOAD_IPROC(vkBindImageMemory);
    LOAD_IPROC(vkCreateBuffer);
    LOAD_IPROC(vkDestroyBuffer);
    LOAD_IPROC(vkGetBufferMemoryRequirements);
    LOAD_IPROC(vkBindBufferMemory);
    LOAD_IPROC(vkMapMemory);
    LOAD_IPROC(vkUnmapMemory);
    LOAD_IPROC(vkCreateRenderPass);
    LOAD_IPROC(vkDestroyRenderPass);
    LOAD_IPROC(vkCreateShaderModule);
    LOAD_IPROC(vkDestroyShaderModule);
    LOAD_IPROC(vkCreatePipelineLayout);
    LOAD_IPROC(vkDestroyPipelineLayout);
    LOAD_IPROC(vkCreateGraphicsPipelines);
    LOAD_IPROC(vkDestroyPipeline);
    LOAD_IPROC(vkCreateFramebuffer);
    LOAD_IPROC(vkDestroyFramebuffer);
    LOAD_IPROC(vkCreateCommandPool);
    LOAD_IPROC(vkDestroyCommandPool);
    LOAD_IPROC(vkAllocateCommandBuffers);
    LOAD_IPROC(vkResetCommandBuffer);
    LOAD_IPROC(vkBeginCommandBuffer);
    LOAD_IPROC(vkEndCommandBuffer);
    LOAD_IPROC(vkCmdBeginRenderPass);
    LOAD_IPROC(vkCmdEndRenderPass);
    LOAD_IPROC(vkCmdBindPipeline);
    LOAD_IPROC(vkCmdSetViewport);
    LOAD_IPROC(vkCmdSetScissor);
    LOAD_IPROC(vkCmdBindVertexBuffers);
    LOAD_IPROC(vkCmdBindIndexBuffer);
    LOAD_IPROC(vkCmdPushConstants);
    LOAD_IPROC(vkCmdDrawIndexed);
    LOAD_IPROC(vkCreateSemaphore);
    LOAD_IPROC(vkDestroySemaphore);
    LOAD_IPROC(vkCreateFence);
    LOAD_IPROC(vkDestroyFence);
    LOAD_IPROC(vkWaitForFences);
    LOAD_IPROC(vkResetFences);
    LOAD_IPROC(vkQueueSubmit);
    LOAD_IPROC(vkGetDeviceProcAddr);
    LOAD_IPROC(vkCreateSampler);
    LOAD_IPROC(vkDestroySampler);
    LOAD_IPROC(vkCreateDescriptorSetLayout);
    LOAD_IPROC(vkDestroyDescriptorSetLayout);
    LOAD_IPROC(vkCreateDescriptorPool);
    LOAD_IPROC(vkDestroyDescriptorPool);
    LOAD_IPROC(vkAllocateDescriptorSets);
    LOAD_IPROC(vkUpdateDescriptorSets);
    LOAD_IPROC(vkCmdBindDescriptorSets);
    LOAD_IPROC(vkCmdDraw);
    LOAD_IPROC(vkCmdPipelineBarrier);
    LOAD_IPROC(vkCmdCopyBufferToImage);
    #undef LOAD_IPROC
    return 1;
}

static void _spec_vk_destroy_swapchain_resources(SpecVulkanCtx* ctx) {
    if (!ctx || !ctx->device) return;
    if (ctx->framebuffers) {
        for (uint32_t i = 0; i < ctx->image_count; i++) {
            if (ctx->framebuffers[i]) ctx->vkDestroyFramebuffer(ctx->device, ctx->framebuffers[i], NULL);
        }
        free(ctx->framebuffers);
        ctx->framebuffers = NULL;
    }
    if (ctx->swap_views) {
        for (uint32_t i = 0; i < ctx->image_count; i++) {
            if (ctx->swap_views[i]) ctx->vkDestroyImageView(ctx->device, ctx->swap_views[i], NULL);
        }
        free(ctx->swap_views);
        ctx->swap_views = NULL;
    }
    if (ctx->swap_images) {
        free(ctx->swap_images);
        ctx->swap_images = NULL;
    }
    ctx->image_count = 0;
    if (ctx->depth_view) { ctx->vkDestroyImageView(ctx->device, ctx->depth_view, NULL); ctx->depth_view = 0; }
    if (ctx->depth_image) { ctx->vkDestroyImage(ctx->device, ctx->depth_image, NULL); ctx->depth_image = 0; }
    if (ctx->depth_mem) { ctx->vkFreeMemory(ctx->device, ctx->depth_mem, NULL); ctx->depth_mem = 0; }
    if (ctx->swapchain) { ctx->vkDestroySwapchainKHR(ctx->device, ctx->swapchain, NULL); ctx->swapchain = 0; }
}

static int _spec_vk_create_swapchain_resources(SpecVulkanCtx* ctx, uint32_t req_w, uint32_t req_h) {
    SpecVkSurfaceCapabilitiesKHR caps;
    if (ctx->vkGetPhysicalDeviceSurfaceCapabilitiesKHR(ctx->phys, ctx->surface, &caps) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkGetPhysicalDeviceSurfaceCapabilitiesKHR failed");
        return 0;
    }

    SpecVkExtent2D ext;
    if (caps.currentExtent.width != ~0U) {
        ext = caps.currentExtent;
    } else {
        ext.width = req_w > 0 ? req_w : 800;
        ext.height = req_h > 0 ? req_h : 600;
        if (ext.width < caps.minImageExtent.width) ext.width = caps.minImageExtent.width;
        if (ext.width > caps.maxImageExtent.width) ext.width = caps.maxImageExtent.width;
        if (ext.height < caps.minImageExtent.height) ext.height = caps.minImageExtent.height;
        if (ext.height > caps.maxImageExtent.height) ext.height = caps.maxImageExtent.height;
    }
    if (ext.width == 0) ext.width = req_w > 0 ? req_w : 1;
    if (ext.height == 0) ext.height = req_h > 0 ? req_h : 1;
    ctx->extent = ext;

    uint32_t min_imgs = caps.minImageCount + 1;
    if (caps.maxImageCount > 0 && min_imgs > caps.maxImageCount) min_imgs = caps.maxImageCount;

    SpecVkSwapchainCreateInfoKHR sci;
    memset(&sci, 0, sizeof(sci));
    sci.sType = SPEC_VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
    sci.surface = ctx->surface;
    sci.minImageCount = min_imgs;
    sci.imageFormat = ctx->color_format;
    sci.imageColorSpace = ctx->color_space;
    sci.imageExtent = ext;
    sci.imageArrayLayers = 1;
    sci.imageUsage = SPEC_VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
    sci.imageSharingMode = SPEC_VK_SHARING_MODE_EXCLUSIVE;
    sci.preTransform = (caps.currentTransform != 0) ? caps.currentTransform : SPEC_VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR;
    sci.compositeAlpha = SPEC_VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
    sci.presentMode = SPEC_VK_PRESENT_MODE_FIFO_KHR;
    sci.clipped = SPEC_VK_TRUE;

    if (ctx->vkCreateSwapchainKHR(ctx->device, &sci, NULL, &ctx->swapchain) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateSwapchainKHR failed");
        return 0;
    }

    uint32_t cnt = 0;
    ctx->vkGetSwapchainImagesKHR(ctx->device, ctx->swapchain, &cnt, NULL);
    if (cnt == 0) {
        _spec_vk_set_error("Swapchain returned 0 images");
        return 0;
    }
    ctx->image_count = cnt;
    ctx->swap_images = (SpecVkImage*)calloc(cnt, sizeof(SpecVkImage));
    ctx->swap_views = (SpecVkImageView*)calloc(cnt, sizeof(SpecVkImageView));
    ctx->framebuffers = (SpecVkFramebuffer*)calloc(cnt, sizeof(SpecVkFramebuffer));
    ctx->vkGetSwapchainImagesKHR(ctx->device, ctx->swapchain, &cnt, ctx->swap_images);

    for (uint32_t i = 0; i < cnt; i++) {
        SpecVkImageViewCreateInfo vci;
        memset(&vci, 0, sizeof(vci));
        vci.sType = SPEC_VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        vci.image = ctx->swap_images[i];
        vci.viewType = SPEC_VK_IMAGE_VIEW_TYPE_2D;
        vci.format = ctx->color_format;
        vci.subresourceRange.aspectMask = SPEC_VK_IMAGE_ASPECT_COLOR_BIT;
        vci.subresourceRange.levelCount = 1;
        vci.subresourceRange.layerCount = 1;
        if (ctx->vkCreateImageView(ctx->device, &vci, NULL, &ctx->swap_views[i]) != SPEC_VK_SUCCESS) {
            _spec_vk_set_error("vkCreateImageView(color) failed");
            return 0;
        }
    }

    /* Depth image */
    SpecVkImageCreateInfo dici;
    memset(&dici, 0, sizeof(dici));
    dici.sType = SPEC_VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    dici.imageType = SPEC_VK_IMAGE_TYPE_2D;
    dici.format = SPEC_VK_FORMAT_D32_SFLOAT;
    dici.extent.width = ext.width;
    dici.extent.height = ext.height;
    dici.extent.depth = 1;
    dici.mipLevels = 1;
    dici.arrayLayers = 1;
    dici.samples = SPEC_VK_SAMPLE_COUNT_1_BIT;
    dici.tiling = SPEC_VK_IMAGE_TILING_OPTIMAL;
    dici.usage = SPEC_VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT;
    dici.sharingMode = SPEC_VK_SHARING_MODE_EXCLUSIVE;
    dici.initialLayout = SPEC_VK_IMAGE_LAYOUT_UNDEFINED;
    if (ctx->vkCreateImage(ctx->device, &dici, NULL, &ctx->depth_image) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateImage(depth) failed");
        return 0;
    }

    SpecVkMemoryRequirements dreq;
    ctx->vkGetImageMemoryRequirements(ctx->device, ctx->depth_image, &dreq);
    uint32_t dmem_idx = _spec_vk_find_memory_type(ctx, dreq.memoryTypeBits, SPEC_VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    if (dmem_idx == ~0U) {
        _spec_vk_set_error("No device local memory for depth");
        return 0;
    }
    SpecVkMemoryAllocateInfo dai;
    memset(&dai, 0, sizeof(dai));
    dai.sType = SPEC_VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    dai.allocationSize = dreq.size;
    dai.memoryTypeIndex = dmem_idx;
    if (ctx->vkAllocateMemory(ctx->device, &dai, NULL, &ctx->depth_mem) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkAllocateMemory(depth) failed");
        return 0;
    }
    ctx->vkBindImageMemory(ctx->device, ctx->depth_image, ctx->depth_mem, 0);

    SpecVkImageViewCreateInfo dvci;
    memset(&dvci, 0, sizeof(dvci));
    dvci.sType = SPEC_VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    dvci.image = ctx->depth_image;
    dvci.viewType = SPEC_VK_IMAGE_VIEW_TYPE_2D;
    dvci.format = SPEC_VK_FORMAT_D32_SFLOAT;
    dvci.subresourceRange.aspectMask = SPEC_VK_IMAGE_ASPECT_DEPTH_BIT;
    dvci.subresourceRange.levelCount = 1;
    dvci.subresourceRange.layerCount = 1;
    if (ctx->vkCreateImageView(ctx->device, &dvci, NULL, &ctx->depth_view) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateImageView(depth) failed");
        return 0;
    }

    for (uint32_t i = 0; i < cnt; i++) {
        SpecVkImageView attachments[2] = { ctx->swap_views[i], ctx->depth_view };
        SpecVkFramebufferCreateInfo fci;
        memset(&fci, 0, sizeof(fci));
        fci.sType = SPEC_VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        fci.renderPass = ctx->render_pass;
        fci.attachmentCount = 2;
        fci.pAttachments = attachments;
        fci.width = ext.width;
        fci.height = ext.height;
        fci.layers = 1;
        if (ctx->vkCreateFramebuffer(ctx->device, &fci, NULL, &ctx->framebuffers[i]) != SPEC_VK_SUCCESS) {
            _spec_vk_set_error("vkCreateFramebuffer failed");
            return 0;
        }
    }
    return 1;
}

static int _spec_vk_create_buffer(SpecVulkanCtx* ctx, SpecVkDeviceSize size, uint32_t usage, const void* data, SpecVkBuffer* out_buf, SpecVkDeviceMemory* out_mem) {
    SpecVkBufferCreateInfo bci;
    memset(&bci, 0, sizeof(bci));
    bci.sType = SPEC_VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
    bci.size = size;
    bci.usage = usage;
    bci.sharingMode = SPEC_VK_SHARING_MODE_EXCLUSIVE;
    if (ctx->vkCreateBuffer(ctx->device, &bci, NULL, out_buf) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateBuffer failed");
        return 0;
    }
    SpecVkMemoryRequirements req;
    ctx->vkGetBufferMemoryRequirements(ctx->device, *out_buf, &req);
    uint32_t mt = _spec_vk_find_memory_type(ctx, req.memoryTypeBits, SPEC_VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | SPEC_VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    if (mt == ~0U) {
        _spec_vk_set_error("No host-visible memory type");
        return 0;
    }
    SpecVkMemoryAllocateInfo mai;
    memset(&mai, 0, sizeof(mai));
    mai.sType = SPEC_VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
    mai.allocationSize = req.size;
    mai.memoryTypeIndex = mt;
    if (ctx->vkAllocateMemory(ctx->device, &mai, NULL, out_mem) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkAllocateMemory(buffer) failed");
        return 0;
    }
    ctx->vkBindBufferMemory(ctx->device, *out_buf, *out_mem, 0);
    if (data && size > 0) {
        void* mapped = NULL;
        if (ctx->vkMapMemory(ctx->device, *out_mem, 0, size, 0, &mapped) != SPEC_VK_SUCCESS) {
            _spec_vk_set_error("vkMapMemory failed");
            return 0;
        }
        memcpy(mapped, data, (size_t)size);
        ctx->vkUnmapMemory(ctx->device, *out_mem);
    }
    return 1;
}

long long spec_pal_vulkan_destroy(long long handle);

long long spec_pal_vulkan_create(
    long long wl_display,
    long long wl_surface,
    long long width,
    long long height,
    long long vert_spv_ptr,
    long long vert_spv_bytes,
    long long frag_spv_ptr,
    long long frag_spv_bytes
) {
    _spec_vk_set_error(NULL);
    if (!wl_display || !wl_surface) {
        _spec_vk_set_error("Null Wayland display or surface");
        return 0;
    }
    if (!vert_spv_ptr || vert_spv_bytes <= 0 || !frag_spv_ptr || frag_spv_bytes <= 0) {
        _spec_vk_set_error("Invalid SPIR-V shader buffer");
        return 0;
    }

    SpecVulkanCtx* ctx = (SpecVulkanCtx*)calloc(1, sizeof(SpecVulkanCtx));
    if (!ctx) { _spec_vk_set_error("OOM"); return 0; }
    if (!_spec_vk_load_procs(ctx)) { free(ctx); return 0; }

    SpecVkApplicationInfo app;
    memset(&app, 0, sizeof(app));
    app.sType = SPEC_VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app.pApplicationName = "SpecSuitShape3D";
    app.applicationVersion = 1;
    app.pEngineName = "SpecSuit";
    app.engineVersion = 1;
    app.apiVersion = SPEC_VK_MAKE_API_VERSION(0, 1, 0, 0);

    const char* inst_exts[2] = { "VK_KHR_surface", "VK_KHR_wayland_surface" };
    SpecVkInstanceCreateInfo ici;
    memset(&ici, 0, sizeof(ici));
    ici.sType = SPEC_VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    ici.pApplicationInfo = &app;
    ici.enabledExtensionCount = 2;
    ici.ppEnabledExtensionNames = inst_exts;

    if (ctx->vkCreateInstance(&ici, NULL, &ctx->instance) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateInstance failed");
        dlclose(ctx->lib);
        free(ctx);
        return 0;
    }
    if (!_spec_vk_load_instance_procs(ctx)) {
        dlclose(ctx->lib);
        free(ctx);
        return 0;
    }

    SpecVkWaylandSurfaceCreateInfoKHR wsci;
    memset(&wsci, 0, sizeof(wsci));
    wsci.sType = SPEC_VK_STRUCTURE_TYPE_WAYLAND_SURFACE_CREATE_INFO_KHR;
    wsci.display = (void*)(intptr_t)wl_display;
    wsci.surface = (void*)(intptr_t)wl_surface;
    if (ctx->vkCreateWaylandSurfaceKHR(ctx->instance, &wsci, NULL, &ctx->surface) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateWaylandSurfaceKHR failed");
        goto fail;
    }

    uint32_t dev_count = 0;
    ctx->vkEnumeratePhysicalDevices(ctx->instance, &dev_count, NULL);
    if (dev_count == 0) {
        _spec_vk_set_error("No Vulkan physical devices found");
        goto fail;
    }
    SpecVkPhysicalDevice* devs = (SpecVkPhysicalDevice*)calloc(dev_count, sizeof(SpecVkPhysicalDevice));
    ctx->vkEnumeratePhysicalDevices(ctx->instance, &dev_count, devs);

    int found = 0;
    for (uint32_t d = 0; d < dev_count && !found; d++) {
        uint32_t qf_count = 0;
        ctx->vkGetPhysicalDeviceQueueFamilyProperties(devs[d], &qf_count, NULL);
        if (qf_count == 0) continue;
        SpecVkQueueFamilyProperties* qfs = (SpecVkQueueFamilyProperties*)calloc(qf_count, sizeof(SpecVkQueueFamilyProperties));
        ctx->vkGetPhysicalDeviceQueueFamilyProperties(devs[d], &qf_count, qfs);
        for (uint32_t q = 0; q < qf_count; q++) {
            SpecVkBool32 present_ok = 0;
            ctx->vkGetPhysicalDeviceSurfaceSupportKHR(devs[d], q, ctx->surface, &present_ok);
            if ((qfs[q].queueFlags & SPEC_VK_QUEUE_GRAPHICS_BIT) && present_ok) {
                ctx->phys = devs[d];
                ctx->queue_family = q;
                found = 1;
                break;
            }
        }
        free(qfs);
    }
    free(devs);
    if (!found) {
        _spec_vk_set_error("No physical device with graphics + Wayland present queue");
        goto fail;
    }

    float q_prio = 1.0f;
    SpecVkDeviceQueueCreateInfo dqci;
    memset(&dqci, 0, sizeof(dqci));
    dqci.sType = SPEC_VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    dqci.queueFamilyIndex = ctx->queue_family;
    dqci.queueCount = 1;
    dqci.pQueuePriorities = &q_prio;

    const char* dev_exts[1] = { "VK_KHR_swapchain" };
    SpecVkDeviceCreateInfo dci;
    memset(&dci, 0, sizeof(dci));
    dci.sType = SPEC_VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    dci.queueCreateInfoCount = 1;
    dci.pQueueCreateInfos = &dqci;
    dci.enabledExtensionCount = 1;
    dci.ppEnabledExtensionNames = dev_exts;
    if (ctx->vkCreateDevice(ctx->phys, &dci, NULL, &ctx->device) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateDevice failed");
        goto fail;
    }
    if (ctx->vkGetDeviceProcAddr) {
        #define LOAD_DPROC(fn) do { \
            void* p = ctx->vkGetDeviceProcAddr(ctx->device, #fn); \
            if (p) ctx->fn = (PFN_spec_##fn)p; \
        } while (0)
        LOAD_DPROC(vkCreateSwapchainKHR);
        LOAD_DPROC(vkDestroySwapchainKHR);
        LOAD_DPROC(vkGetSwapchainImagesKHR);
        LOAD_DPROC(vkAcquireNextImageKHR);
        LOAD_DPROC(vkQueuePresentKHR);
        LOAD_DPROC(vkDeviceWaitIdle);
        #undef LOAD_DPROC
    }
    ctx->vkGetDeviceQueue(ctx->device, ctx->queue_family, 0, &ctx->queue);

    /* Surface format */
    uint32_t fmt_count = 0;
    ctx->vkGetPhysicalDeviceSurfaceFormatsKHR(ctx->phys, ctx->surface, &fmt_count, NULL);
    ctx->color_format = SPEC_VK_FORMAT_B8G8R8A8_UNORM;
    ctx->color_space = SPEC_VK_COLOR_SPACE_SRGB_NONLINEAR_KHR;
    if (fmt_count > 0) {
        SpecVkSurfaceFormatKHR* fmts = (SpecVkSurfaceFormatKHR*)calloc(fmt_count, sizeof(SpecVkSurfaceFormatKHR));
        ctx->vkGetPhysicalDeviceSurfaceFormatsKHR(ctx->phys, ctx->surface, &fmt_count, fmts);
        ctx->color_format = fmts[0].format;
        ctx->color_space = fmts[0].colorSpace;
        for (uint32_t i = 0; i < fmt_count; i++) {
            if (fmts[i].format == SPEC_VK_FORMAT_B8G8R8A8_SRGB && fmts[i].colorSpace == SPEC_VK_COLOR_SPACE_SRGB_NONLINEAR_KHR) {
                ctx->color_format = fmts[i].format;
                ctx->color_space = fmts[i].colorSpace;
                break;
            }
        }
        free(fmts);
    }

    /* Render pass (color + depth) */
    SpecVkAttachmentDescription atts[2];
    memset(atts, 0, sizeof(atts));
    atts[0].format = ctx->color_format;
    atts[0].samples = SPEC_VK_SAMPLE_COUNT_1_BIT;
    atts[0].loadOp = SPEC_VK_ATTACHMENT_LOAD_OP_CLEAR;
    atts[0].storeOp = SPEC_VK_ATTACHMENT_STORE_OP_STORE;
    atts[0].stencilLoadOp = SPEC_VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    atts[0].stencilStoreOp = SPEC_VK_ATTACHMENT_STORE_OP_DONT_CARE;
    atts[0].initialLayout = SPEC_VK_IMAGE_LAYOUT_UNDEFINED;
    atts[0].finalLayout = SPEC_VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;

    atts[1].format = SPEC_VK_FORMAT_D32_SFLOAT;
    atts[1].samples = SPEC_VK_SAMPLE_COUNT_1_BIT;
    atts[1].loadOp = SPEC_VK_ATTACHMENT_LOAD_OP_CLEAR;
    atts[1].storeOp = SPEC_VK_ATTACHMENT_STORE_OP_DONT_CARE;
    atts[1].stencilLoadOp = SPEC_VK_ATTACHMENT_LOAD_OP_DONT_CARE;
    atts[1].stencilStoreOp = SPEC_VK_ATTACHMENT_STORE_OP_DONT_CARE;
    atts[1].initialLayout = SPEC_VK_IMAGE_LAYOUT_UNDEFINED;
    atts[1].finalLayout = SPEC_VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;

    SpecVkAttachmentReference color_ref = { 0, SPEC_VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL };
    SpecVkAttachmentReference depth_ref = { 1, SPEC_VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL };
    SpecVkSubpassDescription subpass;
    memset(&subpass, 0, sizeof(subpass));
    subpass.pipelineBindPoint = SPEC_VK_PIPELINE_BIND_POINT_GRAPHICS;
    subpass.colorAttachmentCount = 1;
    subpass.pColorAttachments = &color_ref;
    subpass.pDepthStencilAttachment = &depth_ref;

    SpecVkSubpassDependency dep;
    memset(&dep, 0, sizeof(dep));
    dep.srcSubpass = SPEC_VK_SUBPASS_EXTERNAL;
    dep.dstSubpass = 0;
    dep.srcStageMask = SPEC_VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT | SPEC_VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT;
    dep.dstStageMask = SPEC_VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT | SPEC_VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT;
    dep.dstAccessMask = SPEC_VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT | SPEC_VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;

    SpecVkRenderPassCreateInfo rpci;
    memset(&rpci, 0, sizeof(rpci));
    rpci.sType = SPEC_VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
    rpci.attachmentCount = 2;
    rpci.pAttachments = atts;
    rpci.subpassCount = 1;
    rpci.pSubpasses = &subpass;
    rpci.dependencyCount = 1;
    rpci.pDependencies = &dep;
    if (ctx->vkCreateRenderPass(ctx->device, &rpci, NULL, &ctx->render_pass) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateRenderPass failed");
        goto fail;
    }

    if (!_spec_vk_create_swapchain_resources(ctx, (uint32_t)width, (uint32_t)height)) {
        goto fail;
    }

    /* Shader modules */
    SpecVkShaderModuleCreateInfo vsmci;
    memset(&vsmci, 0, sizeof(vsmci));
    vsmci.sType = SPEC_VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    vsmci.codeSize = (size_t)vert_spv_bytes;
    vsmci.pCode = (const uint32_t*)(intptr_t)vert_spv_ptr;
    if (ctx->vkCreateShaderModule(ctx->device, &vsmci, NULL, &ctx->vert_mod) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateShaderModule(vert) failed");
        goto fail;
    }

    SpecVkShaderModuleCreateInfo fsmci;
    memset(&fsmci, 0, sizeof(fsmci));
    fsmci.sType = SPEC_VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    fsmci.codeSize = (size_t)frag_spv_bytes;
    fsmci.pCode = (const uint32_t*)(intptr_t)frag_spv_ptr;
    if (ctx->vkCreateShaderModule(ctx->device, &fsmci, NULL, &ctx->frag_mod) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateShaderModule(frag) failed");
        goto fail;
    }

    SpecVkPushConstantRange pcr = { SPEC_VK_SHADER_STAGE_VERTEX_BIT, 0, 64 };
    SpecVkPipelineLayoutCreateInfo plci;
    memset(&plci, 0, sizeof(plci));
    plci.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    plci.pushConstantRangeCount = 1;
    plci.pPushConstantRanges = &pcr;
    if (ctx->vkCreatePipelineLayout(ctx->device, &plci, NULL, &ctx->pipe_layout) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreatePipelineLayout failed");
        goto fail;
    }

    SpecVkPipelineShaderStageCreateInfo stages[2];
    memset(stages, 0, sizeof(stages));
    stages[0].sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[0].stage = SPEC_VK_SHADER_STAGE_VERTEX_BIT;
    stages[0].module = ctx->vert_mod;
    stages[0].pName = "main";
    stages[1].sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stages[1].stage = SPEC_VK_SHADER_STAGE_FRAGMENT_BIT;
    stages[1].module = ctx->frag_mod;
    stages[1].pName = "main";

    SpecVkVertexInputBindingDescription vbind = { 0, 24, SPEC_VK_VERTEX_INPUT_RATE_VERTEX };
    SpecVkVertexInputAttributeDescription vattrs[2] = {
        { 0, 0, SPEC_VK_FORMAT_R32G32B32_SFLOAT, 0 },
        { 1, 0, SPEC_VK_FORMAT_R32G32B32_SFLOAT, 12 }
    };
    SpecVkPipelineVertexInputStateCreateInfo vi;
    memset(&vi, 0, sizeof(vi));
    vi.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vi.vertexBindingDescriptionCount = 1;
    vi.pVertexBindingDescriptions = &vbind;
    vi.vertexAttributeDescriptionCount = 2;
    vi.pVertexAttributeDescriptions = vattrs;

    SpecVkPipelineInputAssemblyStateCreateInfo ia;
    memset(&ia, 0, sizeof(ia));
    ia.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia.topology = SPEC_VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    SpecVkPipelineViewportStateCreateInfo vp;
    memset(&vp, 0, sizeof(vp));
    vp.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    vp.viewportCount = 1;
    vp.scissorCount = 1;

    SpecVkPipelineRasterizationStateCreateInfo rs;
    memset(&rs, 0, sizeof(rs));
    rs.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    rs.polygonMode = SPEC_VK_POLYGON_MODE_FILL;
    rs.cullMode = SPEC_VK_CULL_MODE_BACK_BIT;
    rs.frontFace = SPEC_VK_FRONT_FACE_COUNTER_CLOCKWISE;
    rs.lineWidth = 1.0f;

    SpecVkPipelineMultisampleStateCreateInfo ms;
    memset(&ms, 0, sizeof(ms));
    ms.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms.rasterizationSamples = SPEC_VK_SAMPLE_COUNT_1_BIT;

    SpecVkPipelineDepthStencilStateCreateInfo ds;
    memset(&ds, 0, sizeof(ds));
    ds.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;
    ds.depthTestEnable = SPEC_VK_TRUE;
    ds.depthWriteEnable = SPEC_VK_TRUE;
    ds.depthCompareOp = SPEC_VK_COMPARE_OP_LESS;

    SpecVkPipelineColorBlendAttachmentState cba;
    memset(&cba, 0, sizeof(cba));
    cba.colorWriteMask = 0xFU;
    SpecVkPipelineColorBlendStateCreateInfo cb;
    memset(&cb, 0, sizeof(cb));
    cb.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    cb.attachmentCount = 1;
    cb.pAttachments = &cba;

    uint32_t dyn_states[2] = { SPEC_VK_DYNAMIC_STATE_VIEWPORT, SPEC_VK_DYNAMIC_STATE_SCISSOR };
    SpecVkPipelineDynamicStateCreateInfo dyn;
    memset(&dyn, 0, sizeof(dyn));
    dyn.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    dyn.dynamicStateCount = 2;
    dyn.pDynamicStates = dyn_states;

    SpecVkGraphicsPipelineCreateInfo gpci;
    memset(&gpci, 0, sizeof(gpci));
    gpci.sType = SPEC_VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    gpci.stageCount = 2;
    gpci.pStages = stages;
    gpci.pVertexInputState = &vi;
    gpci.pInputAssemblyState = &ia;
    gpci.pViewportState = &vp;
    gpci.pRasterizationState = &rs;
    gpci.pMultisampleState = &ms;
    gpci.pDepthStencilState = &ds;
    gpci.pColorBlendState = &cb;
    gpci.pDynamicState = &dyn;
    gpci.layout = ctx->pipe_layout;
    gpci.renderPass = ctx->render_pass;
    if (ctx->vkCreateGraphicsPipelines(ctx->device, SPEC_VK_NULL_HANDLE, 1, &gpci, NULL, &ctx->pipeline) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateGraphicsPipelines failed");
        goto fail;
    }

    SpecVkCommandPoolCreateInfo cpci;
    memset(&cpci, 0, sizeof(cpci));
    cpci.sType = SPEC_VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    cpci.flags = SPEC_VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    cpci.queueFamilyIndex = ctx->queue_family;
    if (ctx->vkCreateCommandPool(ctx->device, &cpci, NULL, &ctx->cmd_pool) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkCreateCommandPool failed");
        goto fail;
    }

    SpecVkCommandBufferAllocateInfo cbai;
    memset(&cbai, 0, sizeof(cbai));
    cbai.sType = SPEC_VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    cbai.commandPool = ctx->cmd_pool;
    cbai.level = SPEC_VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cbai.commandBufferCount = 2;
    if (ctx->vkAllocateCommandBuffers(ctx->device, &cbai, ctx->cmd_buf) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkAllocateCommandBuffers failed");
        goto fail;
    }

    SpecVkSemaphoreCreateInfo sci2;
    memset(&sci2, 0, sizeof(sci2));
    sci2.sType = SPEC_VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
    SpecVkFenceCreateInfo fci2;
    memset(&fci2, 0, sizeof(fci2));
    fci2.sType = SPEC_VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    fci2.flags = SPEC_VK_FENCE_CREATE_SIGNALED_BIT;
    for (int f = 0; f < 2; f++) {
        if (ctx->vkCreateSemaphore(ctx->device, &sci2, NULL, &ctx->img_avail_sem[f]) != SPEC_VK_SUCCESS ||
            ctx->vkCreateSemaphore(ctx->device, &sci2, NULL, &ctx->render_done_sem[f]) != SPEC_VK_SUCCESS ||
            ctx->vkCreateFence(ctx->device, &fci2, NULL, &ctx->in_flight_fence[f]) != SPEC_VK_SUCCESS) {
            _spec_vk_set_error("Failed to create sync primitives");
            goto fail;
        }
    }

    ctx->clear_r = 0.08f;
    ctx->clear_g = 0.09f;
    ctx->clear_b = 0.13f;
    ctx->clear_a = 1.0f;

    return (long long)(intptr_t)ctx;

fail:
    spec_pal_vulkan_destroy((long long)(intptr_t)ctx);
    return 0;
}

long long spec_pal_vulkan_set_overlay_pipeline(
    long long handle,
    long long vert_spv_ptr,
    long long vert_spv_bytes,
    long long frag_spv_ptr,
    long long frag_spv_bytes,
    long long quad_ptr,
    long long quad_bytes
) {
    SpecVulkanCtx* ctx = (SpecVulkanCtx*)(intptr_t)handle;
    if (!ctx || !ctx->device || !ctx->render_pass || !vert_spv_ptr || vert_spv_bytes <= 0 || !frag_spv_ptr || frag_spv_bytes <= 0 || !quad_ptr || quad_bytes <= 0) {
        return 0;
    }
    SpecVkShaderModuleCreateInfo ov_vsm = { SPEC_VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO, NULL, 0, (size_t)vert_spv_bytes, (const uint32_t*)(intptr_t)vert_spv_ptr };
    SpecVkShaderModuleCreateInfo ov_fsm = { SPEC_VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO, NULL, 0, (size_t)frag_spv_bytes, (const uint32_t*)(intptr_t)frag_spv_ptr };
    if (ctx->vkCreateShaderModule(ctx->device, &ov_vsm, NULL, &ctx->overlay_vert_mod) != SPEC_VK_SUCCESS ||
        ctx->vkCreateShaderModule(ctx->device, &ov_fsm, NULL, &ctx->overlay_frag_mod) != SPEC_VK_SUCCESS) {
        return 0;
    }
    SpecVkDescriptorSetLayoutBinding dslb = { 0, SPEC_VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1, SPEC_VK_SHADER_STAGE_FRAGMENT_BIT, NULL };
    SpecVkDescriptorSetLayoutCreateInfo dslci = { SPEC_VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO, NULL, 0, 1, &dslb };
    ctx->vkCreateDescriptorSetLayout(ctx->device, &dslci, NULL, &ctx->overlay_desc_layout);

    SpecVkDescriptorPoolSize dps = { SPEC_VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1 };
    SpecVkDescriptorPoolCreateInfo dpci = { SPEC_VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO, NULL, 0, 1, 1, &dps };
    ctx->vkCreateDescriptorPool(ctx->device, &dpci, NULL, &ctx->overlay_desc_pool);

    SpecVkDescriptorSetAllocateInfo dsai = { SPEC_VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO, NULL, ctx->overlay_desc_pool, 1, &ctx->overlay_desc_layout };
    ctx->vkAllocateDescriptorSets(ctx->device, &dsai, &ctx->overlay_desc_set);

    SpecVkSamplerCreateInfo smci;
    memset(&smci, 0, sizeof(smci));
    smci.sType = SPEC_VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
    smci.magFilter = SPEC_VK_FILTER_LINEAR;
    smci.minFilter = SPEC_VK_FILTER_LINEAR;
    smci.addressModeU = SPEC_VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    smci.addressModeV = SPEC_VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    smci.addressModeW = SPEC_VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    ctx->vkCreateSampler(ctx->device, &smci, NULL, &ctx->overlay_sampler);

    SpecVkPipelineLayoutCreateInfo oplci = { SPEC_VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO, NULL, 0, 1, &ctx->overlay_desc_layout, 0, NULL };
    ctx->vkCreatePipelineLayout(ctx->device, &oplci, NULL, &ctx->overlay_pipe_layout);

    SpecVkPipelineShaderStageCreateInfo ostages[2];
    memset(ostages, 0, sizeof(ostages));
    ostages[0].sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    ostages[0].stage = SPEC_VK_SHADER_STAGE_VERTEX_BIT;
    ostages[0].module = ctx->overlay_vert_mod;
    ostages[0].pName = "main";
    ostages[1].sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    ostages[1].stage = SPEC_VK_SHADER_STAGE_FRAGMENT_BIT;
    ostages[1].module = ctx->overlay_frag_mod;
    ostages[1].pName = "main";

    SpecVkVertexInputBindingDescription ov_bind = { 0, 16, SPEC_VK_VERTEX_INPUT_RATE_VERTEX };
    SpecVkVertexInputAttributeDescription ov_attrs[2] = {
        { 0, 0, SPEC_VK_FORMAT_R32G32_SFLOAT, 0 },
        { 1, 0, SPEC_VK_FORMAT_R32G32_SFLOAT, 8 }
    };
    SpecVkPipelineVertexInputStateCreateInfo ov_vi;
    memset(&ov_vi, 0, sizeof(ov_vi));
    ov_vi.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    ov_vi.vertexBindingDescriptionCount = 1;
    ov_vi.pVertexBindingDescriptions = &ov_bind;
    ov_vi.vertexAttributeDescriptionCount = 2;
    ov_vi.pVertexAttributeDescriptions = ov_attrs;

    SpecVkPipelineInputAssemblyStateCreateInfo oia;
    memset(&oia, 0, sizeof(oia));
    oia.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    oia.topology = SPEC_VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    SpecVkPipelineViewportStateCreateInfo ovp;
    memset(&ovp, 0, sizeof(ovp));
    ovp.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    ovp.viewportCount = 1;
    ovp.scissorCount = 1;

    SpecVkPipelineRasterizationStateCreateInfo ov_rs;
    memset(&ov_rs, 0, sizeof(ov_rs));
    ov_rs.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    ov_rs.polygonMode = SPEC_VK_POLYGON_MODE_FILL;
    ov_rs.lineWidth = 1.0f;

    SpecVkPipelineMultisampleStateCreateInfo oms;
    memset(&oms, 0, sizeof(oms));
    oms.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    oms.rasterizationSamples = SPEC_VK_SAMPLE_COUNT_1_BIT;

    SpecVkPipelineDepthStencilStateCreateInfo ov_ds;
    memset(&ov_ds, 0, sizeof(ov_ds));
    ov_ds.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;

    SpecVkPipelineColorBlendAttachmentState ov_cba;
    memset(&ov_cba, 0, sizeof(ov_cba));
    ov_cba.blendEnable = SPEC_VK_TRUE;
    ov_cba.srcColorBlendFactor = SPEC_VK_BLEND_FACTOR_SRC_ALPHA;
    ov_cba.dstColorBlendFactor = SPEC_VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    ov_cba.colorBlendOp = SPEC_VK_BLEND_OP_ADD;
    ov_cba.srcAlphaBlendFactor = SPEC_VK_BLEND_FACTOR_SRC_ALPHA;
    ov_cba.dstAlphaBlendFactor = SPEC_VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    ov_cba.alphaBlendOp = SPEC_VK_BLEND_OP_ADD;
    ov_cba.colorWriteMask = 0xFU;
    SpecVkPipelineColorBlendStateCreateInfo ov_cb;
    memset(&ov_cb, 0, sizeof(ov_cb));
    ov_cb.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    ov_cb.attachmentCount = 1;
    ov_cb.pAttachments = &ov_cba;

    uint32_t odyn_states[2] = { SPEC_VK_DYNAMIC_STATE_VIEWPORT, SPEC_VK_DYNAMIC_STATE_SCISSOR };
    SpecVkPipelineDynamicStateCreateInfo odyn;
    memset(&odyn, 0, sizeof(odyn));
    odyn.sType = SPEC_VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    odyn.dynamicStateCount = 2;
    odyn.pDynamicStates = odyn_states;

    SpecVkGraphicsPipelineCreateInfo ogpci;
    memset(&ogpci, 0, sizeof(ogpci));
    ogpci.sType = SPEC_VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    ogpci.stageCount = 2;
    ogpci.pStages = ostages;
    ogpci.pVertexInputState = &ov_vi;
    ogpci.pInputAssemblyState = &oia;
    ogpci.pViewportState = &ovp;
    ogpci.pRasterizationState = &ov_rs;
    ogpci.pMultisampleState = &oms;
    ogpci.pDepthStencilState = &ov_ds;
    ogpci.pColorBlendState = &ov_cb;
    ogpci.pDynamicState = &odyn;
    ogpci.layout = ctx->overlay_pipe_layout;
    ogpci.renderPass = ctx->render_pass;
    if (ctx->vkCreateGraphicsPipelines(ctx->device, SPEC_VK_NULL_HANDLE, 1, &ogpci, NULL, &ctx->overlay_pipeline) != SPEC_VK_SUCCESS) {
        return 0;
    }
    if (!_spec_vk_create_buffer(ctx, (SpecVkDeviceSize)quad_bytes, SPEC_VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, (const void*)(intptr_t)quad_ptr, &ctx->overlay_vbuf, &ctx->overlay_vmem)) {
        return 0;
    }
    return 1;
}

long long spec_pal_vulkan_set_clear_color(long long handle, double r, double g, double b, double a) {
    SpecVulkanCtx* ctx = (SpecVulkanCtx*)(intptr_t)handle;
    if (!ctx) return 0;
    ctx->clear_r = (float)r;
    ctx->clear_g = (float)g;
    ctx->clear_b = (float)b;
    ctx->clear_a = (float)a;
    return 1;
}

long long spec_pal_vulkan_set_mesh(
    long long handle,
    long long vert_ptr,
    long long vert_bytes,
    long long idx_ptr,
    long long idx_bytes,
    long long idx_count
) {
    SpecVulkanCtx* ctx = (SpecVulkanCtx*)(intptr_t)handle;
    if (!ctx || !ctx->device) { _spec_vk_set_error("Invalid Vulkan handle"); return 0; }
    ctx->vkDeviceWaitIdle(ctx->device);

    if (ctx->vertex_buf) { ctx->vkDestroyBuffer(ctx->device, ctx->vertex_buf, NULL); ctx->vertex_buf = 0; }
    if (ctx->vertex_mem) { ctx->vkFreeMemory(ctx->device, ctx->vertex_mem, NULL); ctx->vertex_mem = 0; }
    if (ctx->index_buf) { ctx->vkDestroyBuffer(ctx->device, ctx->index_buf, NULL); ctx->index_buf = 0; }
    if (ctx->index_mem) { ctx->vkFreeMemory(ctx->device, ctx->index_mem, NULL); ctx->index_mem = 0; }

    if (!_spec_vk_create_buffer(ctx, (SpecVkDeviceSize)vert_bytes, SPEC_VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, (const void*)(intptr_t)vert_ptr, &ctx->vertex_buf, &ctx->vertex_mem)) {
        return 0;
    }
    if (!_spec_vk_create_buffer(ctx, (SpecVkDeviceSize)idx_bytes, SPEC_VK_BUFFER_USAGE_INDEX_BUFFER_BIT, (const void*)(intptr_t)idx_ptr, &ctx->index_buf, &ctx->index_mem)) {
        return 0;
    }
    ctx->index_count = (uint32_t)idx_count;
    return 1;
}

static int _spec_vk_ensure_overlay_resources(SpecVulkanCtx* ctx, uint32_t w, uint32_t h) {
    if (ctx->overlay_img && ctx->overlay_img_w == w && ctx->overlay_img_h == h) return 1;
    ctx->vkDeviceWaitIdle(ctx->device);
    if (ctx->overlay_view) { ctx->vkDestroyImageView(ctx->device, ctx->overlay_view, NULL); ctx->overlay_view = 0; }
    if (ctx->overlay_img) { ctx->vkDestroyImage(ctx->device, ctx->overlay_img, NULL); ctx->overlay_img = 0; }
    if (ctx->overlay_mem) { ctx->vkFreeMemory(ctx->device, ctx->overlay_mem, NULL); ctx->overlay_mem = 0; }
    for (int f = 0; f < 2; f++) {
        if (ctx->overlay_staging_buf[f]) { ctx->vkDestroyBuffer(ctx->device, ctx->overlay_staging_buf[f], NULL); ctx->overlay_staging_buf[f] = 0; }
        if (ctx->overlay_staging_mem[f]) { ctx->vkFreeMemory(ctx->device, ctx->overlay_staging_mem[f], NULL); ctx->overlay_staging_mem[f] = 0; }
    }

    SpecVkDeviceSize byte_size = (SpecVkDeviceSize)w * (SpecVkDeviceSize)h * 4ULL;
    for (int f = 0; f < 2; f++) {
        if (!_spec_vk_create_buffer(ctx, byte_size, SPEC_VK_BUFFER_USAGE_TRANSFER_SRC_BIT, NULL, &ctx->overlay_staging_buf[f], &ctx->overlay_staging_mem[f])) {
            return 0;
        }
    }

    SpecVkImageCreateInfo ici;
    memset(&ici, 0, sizeof(ici));
    ici.sType = SPEC_VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
    ici.imageType = SPEC_VK_IMAGE_TYPE_2D;
    ici.format = ctx->color_format;
    ici.extent.width = w;
    ici.extent.height = h;
    ici.extent.depth = 1;
    ici.mipLevels = 1;
    ici.arrayLayers = 1;
    ici.samples = SPEC_VK_SAMPLE_COUNT_1_BIT;
    ici.tiling = SPEC_VK_IMAGE_TILING_OPTIMAL;
    ici.usage = SPEC_VK_IMAGE_USAGE_TRANSFER_DST_BIT | SPEC_VK_IMAGE_USAGE_SAMPLED_BIT;
    ici.sharingMode = SPEC_VK_SHARING_MODE_EXCLUSIVE;
    ici.initialLayout = SPEC_VK_IMAGE_LAYOUT_UNDEFINED;
    if (ctx->vkCreateImage(ctx->device, &ici, NULL, &ctx->overlay_img) != SPEC_VK_SUCCESS) return 0;

    SpecVkMemoryRequirements req;
    ctx->vkGetImageMemoryRequirements(ctx->device, ctx->overlay_img, &req);
    uint32_t mt = _spec_vk_find_memory_type(ctx, req.memoryTypeBits, SPEC_VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
    if (mt == ~0U) return 0;
    SpecVkMemoryAllocateInfo mai = { SPEC_VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, NULL, req.size, mt };
    if (ctx->vkAllocateMemory(ctx->device, &mai, NULL, &ctx->overlay_mem) != SPEC_VK_SUCCESS) return 0;
    ctx->vkBindImageMemory(ctx->device, ctx->overlay_img, ctx->overlay_mem, 0);

    SpecVkImageViewCreateInfo ivci;
    memset(&ivci, 0, sizeof(ivci));
    ivci.sType = SPEC_VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
    ivci.image = ctx->overlay_img;
    ivci.viewType = SPEC_VK_IMAGE_VIEW_TYPE_2D;
    ivci.format = ctx->color_format;
    ivci.subresourceRange.aspectMask = SPEC_VK_IMAGE_ASPECT_COLOR_BIT;
    ivci.subresourceRange.levelCount = 1;
    ivci.subresourceRange.layerCount = 1;
    if (ctx->vkCreateImageView(ctx->device, &ivci, NULL, &ctx->overlay_view) != SPEC_VK_SUCCESS) return 0;

    SpecVkDescriptorImageInfo dii = { ctx->overlay_sampler, ctx->overlay_view, SPEC_VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL };
    SpecVkWriteDescriptorSet wds;
    memset(&wds, 0, sizeof(wds));
    wds.sType = SPEC_VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    wds.dstSet = ctx->overlay_desc_set;
    wds.descriptorCount = 1;
    wds.descriptorType = SPEC_VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
    wds.pImageInfo = &dii;
    ctx->vkUpdateDescriptorSets(ctx->device, 1, &wds, 0, NULL);

    ctx->overlay_img_w = w;
    ctx->overlay_img_h = h;
    ctx->overlay_img_layout = SPEC_VK_IMAGE_LAYOUT_UNDEFINED;
    return 1;
}

long long spec_pal_vulkan_set_viewport(long long handle, long long x, long long y, long long w, long long h) {
    SpecVulkanCtx* ctx = (SpecVulkanCtx*)(intptr_t)handle;
    if (!ctx) return 0;
    ctx->vp_x = (int32_t)x;
    ctx->vp_y = (int32_t)y;
    ctx->vp_w = (w > 0) ? (uint32_t)w : 0U;
    ctx->vp_h = (h > 0) ? (uint32_t)h : 0U;
    return 1;
}

long long spec_pal_vulkan_render(long long handle, long long mvp_f32_ptr, long long width, long long height) {
    SpecVulkanCtx* ctx = (SpecVulkanCtx*)(intptr_t)handle;
    if (!ctx || !ctx->device || !ctx->swapchain) return 0;

    if (width > 0 && height > 0 && ((uint32_t)width != ctx->extent.width || (uint32_t)height != ctx->extent.height)) {
        ctx->vkDeviceWaitIdle(ctx->device);
        _spec_vk_destroy_swapchain_resources(ctx);
        if (!_spec_vk_create_swapchain_resources(ctx, (uint32_t)width, (uint32_t)height)) return 0;
    }

    uint32_t f = ctx->cur_frame & 1U;
    SpecVkCommandBuffer cmd = ctx->cmd_buf[f];
    ctx->vkWaitForFences(ctx->device, 1, &ctx->in_flight_fence[f], SPEC_VK_TRUE, ~0ULL);
    uint32_t img_idx = 0;
    SpecVkResult acq = ctx->vkAcquireNextImageKHR(ctx->device, ctx->swapchain, ~0ULL, ctx->img_avail_sem[f], SPEC_VK_NULL_HANDLE, &img_idx);
    if (acq == SPEC_VK_ERROR_OUT_OF_DATE_KHR) {
        ctx->vkDeviceWaitIdle(ctx->device);
        _spec_vk_destroy_swapchain_resources(ctx);
        if (!_spec_vk_create_swapchain_resources(ctx, (uint32_t)width, (uint32_t)height)) return 0;
        return 1;
    }
    if (acq != SPEC_VK_SUCCESS && acq != SPEC_VK_SUBOPTIMAL_KHR) {
        _spec_vk_set_error("vkAcquireNextImageKHR failed");
        return 0;
    }

    if (ctx->overlay_dirty && ctx->overlay_cpu_buf && ctx->overlay_w > 0 && ctx->overlay_h > 0) {
        if (!_spec_vk_ensure_overlay_resources(ctx, ctx->overlay_w, ctx->overlay_h)) return 0;
    }

    ctx->vkResetFences(ctx->device, 1, &ctx->in_flight_fence[f]);
    ctx->vkResetCommandBuffer(cmd, 0);

    SpecVkCommandBufferBeginInfo cbi;
    memset(&cbi, 0, sizeof(cbi));
    cbi.sType = SPEC_VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    ctx->vkBeginCommandBuffer(cmd, &cbi);

    if (ctx->overlay_dirty && ctx->overlay_cpu_buf && ctx->overlay_img && ctx->overlay_staging_mem[f]) {
        SpecVkDeviceSize byte_size = (SpecVkDeviceSize)ctx->overlay_w * (SpecVkDeviceSize)ctx->overlay_h * 4ULL;
        void* mapped = NULL;
        if (ctx->vkMapMemory(ctx->device, ctx->overlay_staging_mem[f], 0, byte_size, 0, &mapped) == SPEC_VK_SUCCESS) {
            memcpy(mapped, ctx->overlay_cpu_buf, (size_t)byte_size);
            ctx->vkUnmapMemory(ctx->device, ctx->overlay_staging_mem[f]);

            SpecVkImageMemoryBarrier b1;
            memset(&b1, 0, sizeof(b1));
            b1.sType = SPEC_VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
            b1.srcAccessMask = (ctx->overlay_img_layout == SPEC_VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL) ? SPEC_VK_ACCESS_SHADER_READ_BIT : 0U;
            b1.dstAccessMask = SPEC_VK_ACCESS_TRANSFER_WRITE_BIT;
            b1.oldLayout = ctx->overlay_img_layout;
            b1.newLayout = SPEC_VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            b1.srcQueueFamilyIndex = SPEC_VK_QUEUE_FAMILY_IGNORED;
            b1.dstQueueFamilyIndex = SPEC_VK_QUEUE_FAMILY_IGNORED;
            b1.image = ctx->overlay_img;
            b1.subresourceRange.aspectMask = SPEC_VK_IMAGE_ASPECT_COLOR_BIT;
            b1.subresourceRange.levelCount = 1;
            b1.subresourceRange.layerCount = 1;
            SpecVkFlags src_stage = (ctx->overlay_img_layout == SPEC_VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL) ? SPEC_VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT : SPEC_VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT;
            ctx->vkCmdPipelineBarrier(cmd, src_stage, SPEC_VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, NULL, 0, NULL, 1, &b1);

            SpecVkBufferImageCopy reg;
            memset(&reg, 0, sizeof(reg));
            reg.imageSubresource.aspectMask = SPEC_VK_IMAGE_ASPECT_COLOR_BIT;
            reg.imageSubresource.layerCount = 1;
            reg.imageExtent.width = ctx->overlay_w;
            reg.imageExtent.height = ctx->overlay_h;
            reg.imageExtent.depth = 1;
            ctx->vkCmdCopyBufferToImage(cmd, ctx->overlay_staging_buf[f], ctx->overlay_img, SPEC_VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &reg);

            SpecVkImageMemoryBarrier b2 = b1;
            b2.srcAccessMask = SPEC_VK_ACCESS_TRANSFER_WRITE_BIT;
            b2.dstAccessMask = SPEC_VK_ACCESS_SHADER_READ_BIT;
            b2.oldLayout = SPEC_VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            b2.newLayout = SPEC_VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
            ctx->vkCmdPipelineBarrier(cmd, SPEC_VK_PIPELINE_STAGE_TRANSFER_BIT, SPEC_VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, 0, 0, NULL, 0, NULL, 1, &b2);

            ctx->overlay_img_layout = SPEC_VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
            ctx->overlay_dirty = 0;
        }
    }

    SpecVkClearValue clears[2];
    memset(clears, 0, sizeof(clears));
    clears[0].float32[0] = ctx->clear_r;
    clears[0].float32[1] = ctx->clear_g;
    clears[0].float32[2] = ctx->clear_b;
    clears[0].float32[3] = ctx->clear_a;
    clears[1].depthStencil.depth = 1.0f;
    clears[1].depthStencil.stencil = 0;

    SpecVkRenderPassBeginInfo rpbi;
    memset(&rpbi, 0, sizeof(rpbi));
    rpbi.sType = SPEC_VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
    rpbi.renderPass = ctx->render_pass;
    rpbi.framebuffer = ctx->framebuffers[img_idx];
    rpbi.renderArea.extent = ctx->extent;
    rpbi.clearValueCount = 2;
    rpbi.pClearValues = clears;

    ctx->vkCmdBeginRenderPass(cmd, &rpbi, SPEC_VK_SUBPASS_CONTENTS_INLINE);
    ctx->vkCmdBindPipeline(cmd, SPEC_VK_PIPELINE_BIND_POINT_GRAPHICS, ctx->pipeline);

    SpecVkViewport vp = { 0.0f, 0.0f, (float)ctx->extent.width, (float)ctx->extent.height, 0.0f, 1.0f };
    SpecVkRect2D sc = { {0, 0}, ctx->extent };
    if (ctx->vp_w > 0 && ctx->vp_h > 0) {
        int32_t sx = ctx->vp_x < 0 ? 0 : ctx->vp_x;
        int32_t sy = ctx->vp_y < 0 ? 0 : ctx->vp_y;
        uint32_t sw = ctx->vp_w;
        uint32_t sh = ctx->vp_h;
        if ((uint32_t)sx >= ctx->extent.width) sx = 0;
        if ((uint32_t)sy >= ctx->extent.height) sy = 0;
        if ((uint32_t)sx + sw > ctx->extent.width) sw = ctx->extent.width - (uint32_t)sx;
        if ((uint32_t)sy + sh > ctx->extent.height) sh = ctx->extent.height - (uint32_t)sy;
        vp.x = (float)sx;
        vp.y = (float)sy;
        vp.width = (float)sw;
        vp.height = (float)sh;
        sc.offset.x = sx;
        sc.offset.y = sy;
        sc.extent.width = sw;
        sc.extent.height = sh;
    }
    ctx->vkCmdSetViewport(cmd, 0, 1, &vp);
    ctx->vkCmdSetScissor(cmd, 0, 1, &sc);

    if (mvp_f32_ptr) {
        ctx->vkCmdPushConstants(cmd, ctx->pipe_layout, SPEC_VK_SHADER_STAGE_VERTEX_BIT, 0, 64, (const void*)(intptr_t)mvp_f32_ptr);
    }

    if (ctx->vertex_buf && ctx->index_buf && ctx->index_count > 0) {
        SpecVkDeviceSize offset = 0;
        ctx->vkCmdBindVertexBuffers(cmd, 0, 1, &ctx->vertex_buf, &offset);
        ctx->vkCmdBindIndexBuffer(cmd, ctx->index_buf, 0, SPEC_VK_INDEX_TYPE_UINT16);
        ctx->vkCmdDrawIndexed(cmd, ctx->index_count, 1, 0, 0, 0);
    }

    if (ctx->overlay_ready && ctx->overlay_img && ctx->overlay_pipeline && ctx->overlay_vbuf && ctx->overlay_desc_set) {
        SpecVkViewport full_vp = { 0.0f, 0.0f, (float)ctx->extent.width, (float)ctx->extent.height, 0.0f, 1.0f };
        SpecVkRect2D full_sc = { {0, 0}, ctx->extent };
        ctx->vkCmdSetViewport(cmd, 0, 1, &full_vp);
        ctx->vkCmdSetScissor(cmd, 0, 1, &full_sc);
        SpecVkDeviceSize offset = 0;
        ctx->vkCmdBindPipeline(cmd, SPEC_VK_PIPELINE_BIND_POINT_GRAPHICS, ctx->overlay_pipeline);
        ctx->vkCmdBindDescriptorSets(cmd, SPEC_VK_PIPELINE_BIND_POINT_GRAPHICS, ctx->overlay_pipe_layout, 0, 1, &ctx->overlay_desc_set, 0, NULL);
        ctx->vkCmdBindVertexBuffers(cmd, 0, 1, &ctx->overlay_vbuf, &offset);
        ctx->vkCmdDraw(cmd, 6, 1, 0, 0);
    }

    ctx->vkCmdEndRenderPass(cmd);
    ctx->vkEndCommandBuffer(cmd);

    SpecVkFlags wait_stage = SPEC_VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    SpecVkSubmitInfo si;
    memset(&si, 0, sizeof(si));
    si.sType = SPEC_VK_STRUCTURE_TYPE_SUBMIT_INFO;
    si.waitSemaphoreCount = 1;
    si.pWaitSemaphores = &ctx->img_avail_sem[f];
    si.pWaitDstStageMask = &wait_stage;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &cmd;
    si.signalSemaphoreCount = 1;
    si.pSignalSemaphores = &ctx->render_done_sem[f];
    if (ctx->vkQueueSubmit(ctx->queue, 1, &si, ctx->in_flight_fence[f]) != SPEC_VK_SUCCESS) {
        _spec_vk_set_error("vkQueueSubmit failed");
        return 0;
    }

    SpecVkPresentInfoKHR pi;
    memset(&pi, 0, sizeof(pi));
    pi.sType = SPEC_VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
    pi.waitSemaphoreCount = 1;
    pi.pWaitSemaphores = &ctx->render_done_sem[f];
    pi.swapchainCount = 1;
    pi.pSwapchains = &ctx->swapchain;
    pi.pImageIndices = &img_idx;
    SpecVkResult pres = ctx->vkQueuePresentKHR(ctx->queue, &pi);
    ctx->cur_frame = (f + 1U) & 1U;
    if (pres == SPEC_VK_ERROR_OUT_OF_DATE_KHR || pres == SPEC_VK_SUBOPTIMAL_KHR) {
        ctx->vkDeviceWaitIdle(ctx->device);
        _spec_vk_destroy_swapchain_resources(ctx);
        if (!_spec_vk_create_swapchain_resources(ctx, (uint32_t)width, (uint32_t)height)) return 0;
    }
    return 1;
}

long long spec_pal_vulkan_set_overlay(long long handle, long long pixels_addr, long long width, long long height) {
    SpecVulkanCtx* ctx = (SpecVulkanCtx*)(intptr_t)handle;
    if (!ctx || !ctx->device || !ctx->overlay_desc_set || !pixels_addr || width <= 0 || height <= 0) return 0;

    size_t needed = (size_t)width * (size_t)height * 4U;
    if (needed > ctx->overlay_cpu_bytes) {
        uint8_t* next = (uint8_t*)realloc(ctx->overlay_cpu_buf, needed);
        if (!next) return 0;
        ctx->overlay_cpu_buf = next;
        ctx->overlay_cpu_bytes = needed;
    }
    memcpy(ctx->overlay_cpu_buf, (const void*)(intptr_t)pixels_addr, needed);
    ctx->overlay_w = (uint32_t)width;
    ctx->overlay_h = (uint32_t)height;
    ctx->overlay_dirty = 1;
    ctx->overlay_ready = 1;
    return 1;
}

long long spec_pal_vulkan_destroy(long long handle) {
    SpecVulkanCtx* ctx = (SpecVulkanCtx*)(intptr_t)handle;
    if (!ctx) return 0;
    if (ctx->overlay_cpu_buf) { free(ctx->overlay_cpu_buf); ctx->overlay_cpu_buf = NULL; }
    if (ctx->device) {
        ctx->vkDeviceWaitIdle(ctx->device);
        if (ctx->overlay_view) ctx->vkDestroyImageView(ctx->device, ctx->overlay_view, NULL);
        if (ctx->overlay_img) ctx->vkDestroyImage(ctx->device, ctx->overlay_img, NULL);
        if (ctx->overlay_mem) ctx->vkFreeMemory(ctx->device, ctx->overlay_mem, NULL);
        for (int f = 0; f < 2; f++) {
            if (ctx->overlay_staging_buf[f]) ctx->vkDestroyBuffer(ctx->device, ctx->overlay_staging_buf[f], NULL);
            if (ctx->overlay_staging_mem[f]) ctx->vkFreeMemory(ctx->device, ctx->overlay_staging_mem[f], NULL);
        }
        if (ctx->overlay_vbuf) ctx->vkDestroyBuffer(ctx->device, ctx->overlay_vbuf, NULL);
        if (ctx->overlay_vmem) ctx->vkFreeMemory(ctx->device, ctx->overlay_vmem, NULL);
        if (ctx->overlay_pipeline) ctx->vkDestroyPipeline(ctx->device, ctx->overlay_pipeline, NULL);
        if (ctx->overlay_pipe_layout) ctx->vkDestroyPipelineLayout(ctx->device, ctx->overlay_pipe_layout, NULL);
        if (ctx->overlay_sampler) ctx->vkDestroySampler(ctx->device, ctx->overlay_sampler, NULL);
        if (ctx->overlay_desc_pool) ctx->vkDestroyDescriptorPool(ctx->device, ctx->overlay_desc_pool, NULL);
        if (ctx->overlay_desc_layout) ctx->vkDestroyDescriptorSetLayout(ctx->device, ctx->overlay_desc_layout, NULL);
        if (ctx->overlay_frag_mod) ctx->vkDestroyShaderModule(ctx->device, ctx->overlay_frag_mod, NULL);
        if (ctx->overlay_vert_mod) ctx->vkDestroyShaderModule(ctx->device, ctx->overlay_vert_mod, NULL);
        if (ctx->vertex_buf) ctx->vkDestroyBuffer(ctx->device, ctx->vertex_buf, NULL);
        if (ctx->vertex_mem) ctx->vkFreeMemory(ctx->device, ctx->vertex_mem, NULL);
        if (ctx->index_buf) ctx->vkDestroyBuffer(ctx->device, ctx->index_buf, NULL);
        if (ctx->index_mem) ctx->vkFreeMemory(ctx->device, ctx->index_mem, NULL);
        for (int f = 0; f < 2; f++) {
            if (ctx->in_flight_fence[f]) ctx->vkDestroyFence(ctx->device, ctx->in_flight_fence[f], NULL);
            if (ctx->render_done_sem[f]) ctx->vkDestroySemaphore(ctx->device, ctx->render_done_sem[f], NULL);
            if (ctx->img_avail_sem[f]) ctx->vkDestroySemaphore(ctx->device, ctx->img_avail_sem[f], NULL);
        }
        if (ctx->cmd_pool) ctx->vkDestroyCommandPool(ctx->device, ctx->cmd_pool, NULL);
        if (ctx->pipeline) ctx->vkDestroyPipeline(ctx->device, ctx->pipeline, NULL);
        if (ctx->pipe_layout) ctx->vkDestroyPipelineLayout(ctx->device, ctx->pipe_layout, NULL);
        if (ctx->frag_mod) ctx->vkDestroyShaderModule(ctx->device, ctx->frag_mod, NULL);
        if (ctx->vert_mod) ctx->vkDestroyShaderModule(ctx->device, ctx->vert_mod, NULL);
        _spec_vk_destroy_swapchain_resources(ctx);
        if (ctx->render_pass) ctx->vkDestroyRenderPass(ctx->device, ctx->render_pass, NULL);
        ctx->vkDestroyDevice(ctx->device, NULL);
    }
    if (ctx->surface && ctx->instance) ctx->vkDestroySurfaceKHR(ctx->instance, ctx->surface, NULL);
    if (ctx->instance) ctx->vkDestroyInstance(ctx->instance, NULL);
    if (ctx->lib) dlclose(ctx->lib);
    free(ctx);
    return 1;
}

long long spec_pal_vulkan_last_error(void) {
    return (long long)(intptr_t)_spec_vk_error;
}

#else

long long spec_pal_vulkan_destroy(long long handle);

long long spec_pal_vulkan_create(
    long long wl_display,
    long long wl_surface,
    long long width,
    long long height,
    long long vert_spv_ptr,
    long long vert_spv_bytes,
    long long frag_spv_ptr,
    long long frag_spv_bytes
) {
    (void)wl_display; (void)wl_surface; (void)width; (void)height;
    (void)vert_spv_ptr; (void)vert_spv_bytes; (void)frag_spv_ptr; (void)frag_spv_bytes;
    return 0;
}

long long spec_pal_vulkan_set_mesh(
    long long handle,
    long long vert_ptr,
    long long vert_bytes,
    long long idx_ptr,
    long long idx_bytes,
    long long idx_count
) {
    (void)handle; (void)vert_ptr; (void)vert_bytes; (void)idx_ptr; (void)idx_bytes; (void)idx_count;
    return 0;
}

long long spec_pal_vulkan_render(long long handle, long long mvp_f32_ptr, long long width, long long height) {
    (void)handle; (void)mvp_f32_ptr; (void)width; (void)height;
    return 0;
}

long long spec_pal_vulkan_set_overlay(long long handle, long long pixels_addr, long long width, long long height) {
    (void)handle; (void)pixels_addr; (void)width; (void)height;
    return 0;
}

long long spec_pal_vulkan_set_viewport(long long handle, long long x, long long y, long long w, long long h) {
    (void)handle; (void)x; (void)y; (void)w; (void)h;
    return 0;
}

long long spec_pal_vulkan_set_overlay_pipeline(long long handle, long long vp, long long vb, long long fp, long long fb, long long qp, long long qb) {
    (void)handle; (void)vp; (void)vb; (void)fp; (void)fb; (void)qp; (void)qb;
    return 0;
}

long long spec_pal_vulkan_set_clear_color(long long handle, double r, double g, double b, double a) {
    (void)handle; (void)r; (void)g; (void)b; (void)a;
    return 0;
}

long long spec_pal_vulkan_destroy(long long handle) {
    (void)handle;
    return 0;
}

long long spec_pal_vulkan_last_error(void) {
    return (long long)(intptr_t)"Vulkan surface is only supported on Linux";
}

#endif

long long spec_pal_vulkan_pack_f32(long long dst_ptr, long long byte_offset, double val) {
    if (dst_ptr) {
        float f = (float)val;
        memcpy((char*)(intptr_t)dst_ptr + byte_offset, &f, 4);
    }
    return 0;
}
